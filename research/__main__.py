"""Run with .venv/Scripts/python -m research --help from the repository root."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

from . import ROOT, core, runtime


DEFAULT_DATA = ROOT / "artifacts" / "data" / "pilot"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def new_directory(path):
    path = Path(path)
    if path.exists():
        raise ValueError(f"Output already exists: {path}. Choose a new output to preserve previous work.")
    path.mkdir(parents=True)
    return path


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def load_config(path):
    config = read_json(path)
    if set(config["splits"]) != {"train", "calibration", "development"}:
        raise ValueError("Config needs train, calibration and development split sizes")
    integers = [*config["splits"].values(), config["candidates_per_pool"], config["feedback_attempts"],
                config["answer_budget"], *config["reasoning_budgets"], config["training"]["batch_size"],
                config["training"]["max_length"], config["training"]["gradient_accumulation_steps"],
                config["training"]["lora_rank"], config["training"]["lora_alpha"], config["top_k"]]
    if not config["reasoning_budgets"] or any(type(n) is not int or n <= 0 for n in integers):
        raise ValueError("Counts and token budgets must be positive integers")
    numbers = [config["temperature"], config["training"]["epochs"], config["training"]["learning_rate"]]
    if any(not isinstance(n, (int, float)) or not math.isfinite(n) or n <= 0 for n in numbers):
        raise ValueError("Temperature, epochs and learning rate must be positive finite numbers")
    if not 0 < config["top_p"] <= 1 or not 0 <= config["training"]["lora_dropout"] < 1:
        raise ValueError("top_p or LoRA dropout is out of range")
    if type(config["seed"]) is not int or config["seed"] < 0:
        raise ValueError("Seed must be a nonnegative integer")
    if not isinstance(config["length_penalty"], (int, float)) or not math.isfinite(config["length_penalty"]) or config["length_penalty"] < 0:
        raise ValueError("Length penalty must be finite and nonnegative")
    return config


def load_data(args, config):
    manifest = read_json(args.data / "manifest.json")
    if manifest["model"] != config["model"] or manifest["dataset"] != config["dataset"]:
        raise ValueError("Prepared data uses a different model or dataset; prepare a separate directory")
    for name, expected in manifest["files"].items():
        if digest(args.data / name) != expected:
            raise ValueError(f"Prepared split changed: {name}. Prepare a new directory instead of editing it.")
    return manifest


def record_metadata(config, manifest=None, **extra):
    return {"config": config, "data_manifest": core.data_identity(manifest) if manifest else None,
            "environment": runtime.environment(), **extra}


def prepare(args, config):
    if args.output.exists():
        raise ValueError(f"Output already exists: {args.output}. Choose a new directory.")
    from datasets import load_dataset
    from huggingface_hub import HfApi, snapshot_download

    api = HfApi()
    model_revision = api.model_info(config["model"], revision=config["model_revision"]).sha
    dataset_revision = api.dataset_info(config["dataset"], revision=config["dataset_revision"]).sha
    print("Caching model and GSM8K training pool...", flush=True)
    snapshot_download(config["model"], revision=model_revision,
                      allow_patterns=["*.json", "*.safetensors", "*.txt", "*.jinja", "*.model"])
    dataset = load_dataset(config["dataset"], config["dataset_config"], revision=dataset_revision, split="train")
    rows = []
    for index, row in enumerate(dataset):
        answer = core.extract_answer(row["answer"])
        if answer is None:
            raise ValueError(f"Unparseable GSM8K gold answer at training index {index}")
        rows.append({"id": f"train-{index}", "question": row["question"], "solution": row["answer"], "answer": answer})
    splits = core.make_splits(rows, config["splits"], config["seed"])
    output = new_directory(args.output)
    for name, values in splits.items():
        core.write_jsonl(output / f"{name}.jsonl", values)
    manifest = {"model": config["model"], "model_revision": model_revision, "dataset": config["dataset"],
                "dataset_revision": dataset_revision, "dataset_config": config["dataset_config"],
                "dataset_fingerprint": dataset._fingerprint, "seed": config["seed"],
                "sizes": config["splits"], "ids": {name: [r["id"] for r in values] for name, values in splits.items()},
                "files": {f"{name}.jsonl": digest(output / f"{name}.jsonl") for name in splits},
                "config": config, "environment": runtime.environment()}
    core.write_json(output / "manifest.json", manifest)
    print(f"Prepared {output}; official test examples were not used.")


def ollama_request(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request("http://localhost:11434/api/" + path, data=data,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.load(response)
    except urllib.error.URLError as error:
        raise ValueError("Cannot reach local Ollama. Start it and pull the teacher model, or use --import-file.") from error


def rewrite(args, config):
    manifest = load_data(args, config)
    problems = core.read_jsonl(args.data / f"{args.split}.jsonl")
    problems = problems[:args.limit] if args.limit else problems
    lookup = {p["id"]: p for p in problems}
    output = new_directory(args.output)
    if args.import_file:
        if not args.teacher_label:
            raise ValueError("Imported rewrites require --teacher-label with the exact model/version and prompt provenance")
        candidates = core.read_jsonl(args.import_file)
        teacher = {"provider": "import", "label": args.teacher_label, "source_sha256": digest(args.import_file)}
    else:
        tags = ollama_request("tags")["models"]
        match = next((m for m in tags if m["name"] == args.ollama_model), None)
        if not match:
            raise ValueError(f"Teacher {args.ollama_model} is not installed in Ollama; pull it first")
        teacher = {"provider": "ollama", "model": args.ollama_model, "digest": match["digest"]}
        candidates = []
        with (output / "teacher-responses.jsonl").open("x", encoding="utf-8") as raw:
            for problem in problems:
                for pool in core.POOLS:
                    for index in range(config["candidates_per_pool"]):
                        prompt = (
                            "Rewrite this supplied arithmetic solution more compactly without changing its meaning. "
                            "Preserve every <<expression=result>> calculation exactly, in the same order. "
                            "Use English and equations only. " if pool == "english" else
                            "Rewrite this supplied arithmetic solution more compactly without changing its meaning. "
                            "Preserve every <<expression=result>> calculation exactly, in the same order. "
                            "You may mix English, Mandarin and equations. ")
                        prompt += (
                            'Return JSON only: {"steps":[{"text":"short explanation","equation":"3*5=15"}],"answer":"15"}. '
                            "One step per original annotated calculation. No #### or chat tags in step text. "
                            f"Try alternative phrasing {index + 1}.\nQuestion: {problem['question']}\nSolution: {problem['solution']}")
                        response = ollama_request("chat", {"model": args.ollama_model, "stream": False, "think": False,
                            "format": "json", "messages": [{"role": "user", "content": prompt}],
                            "options": {"seed": config["seed"] + index, "temperature": 0.7, "num_predict": 1024}})
                        raw.write(json.dumps({"id": problem["id"], "pool": pool, "candidate": index,
                                              "prompt": prompt, "response": response}, ensure_ascii=False) + "\n")
                        raw.flush()
                        try:
                            value = json.loads(response["message"]["content"])
                            if not isinstance(value, dict):
                                raise ValueError("Teacher did not return an object")
                        except (json.JSONDecodeError, ValueError):
                            value = {"steps": [], "answer": "invalid"}
                        value.update(id=problem["id"], pool=pool, candidate=index, reviewed=False)
                        candidates.append(value)
                        print(f"Rewrote {problem['id']} {pool} {index}", flush=True)
    seen = set()
    for candidate in candidates:
        if candidate.get("id") not in lookup:
            raise ValueError("Candidate ID is outside the requested training/calibration split")
        key = (candidate["id"], candidate.get("pool"), candidate.get("candidate"))
        if key in seen:
            raise ValueError(f"Duplicate candidate: {key}")
        seen.add(key)
        candidate["reviewed"] = candidate.get("reviewed") is True
        candidate["validation_errors"] = core.validate_candidate(candidate, lookup[candidate["id"]])
    core.write_jsonl(output / "candidates.jsonl", candidates)
    core.write_json(output / "manifest.json", record_metadata(config, manifest, split=args.split, teacher=teacher,
                    source_manifest_sha256=digest(args.data / "manifest.json")))
    print(f"Saved {len(candidates)} candidates; {sum(not c['validation_errors'] for c in candidates)} pass arithmetic/structure checks. Human meaning review is still required.")


def score(args, config):
    manifest = load_data(args, config)
    problems = {r["id"]: r for r in core.read_jsonl(args.data / f"{args.split}.jsonl")}
    candidates = core.read_jsonl(args.candidates)
    if any(c.get("id") not in problems for c in candidates):
        raise ValueError("Candidate IDs are outside the selected split")
    output = new_directory(args.output)
    runner = runtime.ModelRunner(config, manifest)
    results = []
    with (output / "attempts.jsonl").open("x", encoding="utf-8") as attempts:
        for candidate in candidates:
            candidate = dict(candidate)
            candidate.pop("feedback_error", None)
            candidate["validation_errors"] = core.validate_candidate(candidate, problems[candidate["id"]])
            candidate["tokens"] = len(runner.tokenizer.encode(core.render_solution(candidate), add_special_tokens=False)) if not candidate["validation_errors"] else 0
            candidate["feedback_accuracy"] = 0.0
            if not candidate["validation_errors"]:
                try:
                    prefix = core.feedback_prefix(candidate)
                except ValueError as error:
                    candidate["feedback_error"] = str(error)
                else:
                    correct = 0
                    for attempt in range(args.attempts or config["feedback_attempts"]):
                        key = f"{config['seed']}:{candidate['id']}:{candidate['pool']}:{candidate['candidate']}:{attempt}"
                        seed = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
                        prediction = runner.answer(problems[candidate["id"]]["question"], 256, seed, prefix)
                        prediction.update(id=candidate["id"], pool=candidate["pool"], candidate=candidate["candidate"], attempt=attempt,
                                          correct=prediction["predicted_answer"] == problems[candidate["id"]]["answer"])
                        correct += prediction["correct"]
                        attempts.write(json.dumps(prediction, ensure_ascii=False) + "\n")
                        attempts.flush()
                    candidate["feedback_accuracy"] = correct / (args.attempts or config["feedback_attempts"])
            results.append(candidate)
            print(f"Scored {candidate['id']} {candidate['pool']} {candidate['candidate']}", flush=True)
    core.write_jsonl(output / "scored.jsonl", results)
    core.write_json(output / "manifest.json", record_metadata(config, manifest, split=args.split,
                    attempts=args.attempts or config["feedback_attempts"], candidates_sha256=digest(args.candidates)))


def select(args, config):
    manifest = load_data(args, config)
    source = read_json(args.scored.parent / "manifest.json")
    if source["split"] != "train" or source["data_manifest"] != core.data_identity(manifest):
        raise ValueError("Selection requires feedback scores from this prepared training split and model")
    problems = core.read_jsonl(args.data / "train.jsonl")
    groups, excluded = core.select_conditions(problems, core.read_jsonl(args.scored), config["candidates_per_pool"], config["length_penalty"])
    if not groups["original"]:
        raise ValueError("No complete valid problem bundles remain; inspect validation and feedback errors")
    output = new_directory(args.output)
    for condition, rows in groups.items():
        core.write_jsonl(output / f"{condition}.jsonl", rows)
    core.write_jsonl(output / "excluded.jsonl", excluded)
    core.write_json(output / "manifest.json", record_metadata(config, manifest, length_penalty=config["length_penalty"],
                    scored_sha256=digest(args.scored), ids=[r["id"] for r in groups["original"]]))
    print(f"Selected all five conditions on {len(groups['original'])} identical IDs; excluded {len(excluded)} bundles.")


def train(args, config):
    manifest = load_data(args, config)
    originals = {r["id"]: r for r in core.read_jsonl(args.data / "train.jsonl")}
    if args.conditions:
        selected_manifest = read_json(args.conditions / "manifest.json")
        if selected_manifest["data_manifest"] != core.data_identity(manifest):
            raise ValueError("Selected conditions do not match this prepared data")
        rows = core.read_jsonl(args.conditions / f"{args.condition}.jsonl")
        if [r["id"] for r in rows] != selected_manifest["ids"]:
            raise ValueError("Condition no longer has the matched selection IDs")
    elif args.condition == "original":
        rows = list(originals.values())
    else:
        raise ValueError("Rewritten conditions require --conditions from the select command")
    if not rows or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Training needs nonempty, unique question IDs")
    for row in rows:
        original = originals.get(row["id"])
        if not original or row["question"] != original["question"] or row["answer"] != original["answer"]:
            raise ValueError("Training rows must match the original training questions and answers")
        if args.condition == "original":
            if row["solution"] != original["solution"]:
                raise ValueError("Original baseline must use unchanged GSM8K solutions")
        else:
            errors = core.validate_candidate(row, original)
            if errors or row["solution"] != core.render_solution(row):
                raise ValueError(f"Invalid selected solution {row['id']}: {errors}")
            if row.get("reviewed") is not True and not args.allow_unreviewed:
                raise ValueError("Selected rewrites need human meaning review (reviewed: true), or --allow-unreviewed for a labelled screening run")
    output = new_directory(args.output)
    metadata = record_metadata(config, manifest, condition=args.condition, training_ids=[r["id"] for r in rows],
                               smoke_check=args.smoke_steps is not None, unreviewed_screening=args.allow_unreviewed,
                               smoke_steps=args.smoke_steps,
                               conditions_manifest_sha256=digest(args.conditions / "manifest.json") if args.conditions else None)
    core.write_json(output / "request.json", metadata)
    runner = runtime.ModelRunner(config, manifest)
    result = runtime.train_adapter(runner, rows, config, output, args.smoke_steps or -1)
    core.write_json(output / "run.json", dict(metadata, **result, status="complete"))
    print(f"Saved adapter to {output / 'adapter'}")


def freeze(args, config):
    manifest = load_data(args, config)
    core.write_json(args.output, record_metadata(config, manifest))
    print(f"Saved fixed evaluation settings to {args.output}")


def evaluate(args, config):
    if args.budget and args.budget not in config["reasoning_budgets"]:
        raise ValueError("Choose one of the configured reasoning budgets; change the config before freezing settings")
    if args.split == "official-test":
        if not args.final_test:
            raise ValueError("Official test evaluation requires --final-test after development is complete")
        if not args.frozen_settings:
            raise ValueError("Official test evaluation requires --frozen-settings saved after development")
        if args.limit:
            raise ValueError("Official test evaluation requires the full question set; --limit is only for development checks")
    manifest = load_data(args, config)
    if args.frozen_settings:
        frozen = read_json(args.frozen_settings)
        if frozen["config"] != config or frozen["data_manifest"] != core.data_identity(manifest):
            raise ValueError("Settings changed since freezing; do not tune after final testing begins")
    adapter_metadata = None
    if args.adapter:
        adapter_metadata = read_json(args.adapter.parent / "run.json")
        if adapter_metadata["data_manifest"] != core.data_identity(manifest) or adapter_metadata["status"] != "complete":
            raise ValueError("Adapter is incomplete or uses a different prepared model/data revision")
        if args.split == "official-test" and (adapter_metadata["smoke_check"] or adapter_metadata["unreviewed_screening"]):
            raise ValueError("Smoke-check or unreviewed screening adapters cannot be used for final testing")
        if args.split == "official-test" and adapter_metadata["config"]["training"] != config["training"]:
            raise ValueError("Adapter training settings differ from the frozen configuration")
    output = new_directory(args.output)
    if args.split == "official-test":
        from datasets import load_dataset
        dataset = load_dataset(config["dataset"], config["dataset_config"], revision=manifest["dataset_revision"], split="test")
        rows = [{"id": f"test-{i}", "question": r["question"], "answer": core.extract_answer(r["answer"])} for i, r in enumerate(dataset)]
        if any(r["answer"] is None for r in rows):
            raise ValueError("An official gold answer could not be parsed")
    else:
        rows = core.read_jsonl(args.data / "development.jsonl")
    rows = rows[:args.limit] if args.limit else rows
    budgets = [args.budget] if args.budget else config["reasoning_budgets"]
    metadata = record_metadata(config, manifest, split=args.split, budgets=budgets,
                               condition=adapter_metadata["condition"] if adapter_metadata else "unchanged",
                               adapter_run=adapter_metadata, subset=args.limit is not None,
                               question_ids=[r["id"] for r in rows],
                               frozen_settings_sha256=digest(args.frozen_settings) if args.frozen_settings else None)
    core.write_json(output / "manifest.json", metadata)
    runner = runtime.ModelRunner(config, manifest, args.adapter)
    summaries = []
    with (output / "predictions.jsonl").open("x", encoding="utf-8") as destination:
        for budget in budgets:
            measured = []
            for index, row in enumerate(rows):
                started = time.perf_counter()
                seed = config["seed"] + index
                try:
                    result = runner.answer(row["question"], budget, seed)
                except (RuntimeError, ValueError) as error:
                    result = {"output": "", "predicted_answer": None, "output_tokens": None,
                              "seconds": time.perf_counter() - started, "truncated": False,
                              "error": f"{type(error).__name__}: {error}", "seed": seed}
                    if runner.device == "cuda":
                        import torch
                        torch.cuda.empty_cache()
                result.update(id=row["id"], budget=budget, expected_answer=row["answer"],
                              correct=result["predicted_answer"] == row["answer"] and result["predicted_answer"] is not None)
                destination.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
                destination.flush()
                measured.append(result)
                print(f"{budget} tokens: {index + 1}/{len(rows)} correct={result['correct']} error={bool(result['error'])}", flush=True)
            summaries.append(dict(core.summarize(measured), budget=budget))
    core.write_json(output / "summary.json", {"condition": metadata["condition"], "split": args.split, "results": summaries})
    print(json.dumps(summaries, indent=2))


def compare(args, config):
    reference, candidate = read_json(args.reference / "manifest.json"), read_json(args.candidate / "manifest.json")
    for key in ("config", "data_manifest", "split", "budgets", "subset", "question_ids"):
        if reference[key] != candidate[key]:
            raise ValueError(f"Evaluation settings differ: {key}")
    left_adapter, right_adapter = reference.get("adapter_run"), candidate.get("adapter_run")
    if left_adapter and right_adapter:
        if (left_adapter["training_ids"] != right_adapter["training_ids"]
                or left_adapter["config"]["training"] != right_adapter["config"]["training"]
                or left_adapter.get("smoke_steps") != right_adapter.get("smoke_steps")):
            raise ValueError("Adapter training questions or settings differ; use the matched original baseline")
    for path, metadata in ((args.reference, reference), (args.candidate, candidate)):
        if not (path / "summary.json").is_file():
            raise ValueError(f"Evaluation is not complete: {path}")
        summary = read_json(path / "summary.json")
        if {r["budget"] for r in summary["results"]} != set(metadata["budgets"]) or any(
                r["sample_size"] != len(metadata["question_ids"]) for r in summary["results"]):
            raise ValueError(f"Evaluation summary is incomplete: {path}")
    old, new = core.read_jsonl(args.reference / "predictions.jsonl"), core.read_jsonl(args.candidate / "predictions.jsonl")
    for rows in (old, new):
        if len(rows) != len(reference["question_ids"]) * len(reference["budgets"]) or any(
                {r["id"] for r in rows if r["budget"] == budget} != set(reference["question_ids"]) for budget in reference["budgets"]):
            raise ValueError("Evaluation predictions are incomplete")
    results = [dict(core.paired_comparison([r for r in old if r["budget"] == budget],
                                          [r for r in new if r["budget"] == budget], config["seed"]), budget=budget)
               for budget in reference["budgets"]]
    report = {"reference": str(args.reference), "candidate": str(args.candidate), "results": results}
    core.write_json(args.output, report)
    print(json.dumps(report, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compact multilingual reasoning research pipeline")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "pilot.json")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check Python packages and CUDA")
    command = commands.add_parser("prepare", help="Cache model/data and save disjoint training-pool partitions")
    command.add_argument("--output", type=Path, default=DEFAULT_DATA)
    command = commands.add_parser("rewrite", help="Generate with local Ollama or import teacher JSONL")
    command.add_argument("--data", type=Path, default=DEFAULT_DATA)
    command.add_argument("--split", choices=("train", "calibration"), default="train")
    command.add_argument("--limit", type=positive)
    source = command.add_mutually_exclusive_group(required=True)
    source.add_argument("--ollama-model")
    source.add_argument("--import-file", type=Path)
    command.add_argument("--teacher-label")
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("score", help="Score partial-solution candidates with the unchanged model")
    command.add_argument("--data", type=Path, default=DEFAULT_DATA)
    command.add_argument("--split", choices=("train", "calibration"), default="train")
    command.add_argument("--candidates", type=Path, required=True)
    command.add_argument("--attempts", type=positive)
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("select", help="Build all five conditions using identical valid question IDs")
    command.add_argument("--data", type=Path, default=DEFAULT_DATA)
    command.add_argument("--scored", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("train", help="Train one LoRA adapter")
    command.add_argument("--data", type=Path, default=DEFAULT_DATA)
    command.add_argument("--conditions", type=Path)
    command.add_argument("--condition", choices=core.CONDITIONS, default="original")
    command.add_argument("--allow-unreviewed", action="store_true")
    command.add_argument("--smoke-steps", type=positive, help="Short integration check; labels this adapter as a smoke check")
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("freeze", help="Save evaluation settings before opening the official test set")
    command.add_argument("--data", type=Path, default=DEFAULT_DATA)
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("evaluate", help="Evaluate unchanged model or saved adapter on questions alone")
    command.add_argument("--data", type=Path, default=DEFAULT_DATA)
    command.add_argument("--adapter", type=Path)
    command.add_argument("--split", choices=("development", "official-test"), default="development")
    command.add_argument("--final-test", action="store_true")
    command.add_argument("--frozen-settings", type=Path)
    command.add_argument("--limit", type=positive)
    command.add_argument("--budget", type=positive)
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("compare", help="Compare matched runs with paired bootstrap uncertainty")
    command.add_argument("--reference", type=Path, required=True)
    command.add_argument("--candidate", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "doctor":
            result = runtime.environment()
            print(json.dumps(result, indent=2))
            if any(value is None for value in result["packages"].values()):
                raise ValueError("Dependencies are missing; run scripts/setup.ps1")
            if not result.get("cuda_available"):
                raise ValueError("CUDA is unavailable; install the pinned CUDA PyTorch build and check your NVIDIA driver")
        else:
            globals()[args.command](args, config)
    except (ValueError, OSError, KeyError, ImportError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
