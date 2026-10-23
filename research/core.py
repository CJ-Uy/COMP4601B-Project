"""Dataset and scoring operations that do not require a model or GPU."""

import ast
from collections import Counter, defaultdict
from fractions import Fraction
import json
import math
from pathlib import Path
import random
import re
import statistics


POOLS = ("english", "multilingual")
CONDITIONS = ("original", "english-shortest", "english-feedback", "multilingual-shortest", "multilingual-feedback")
NUMBER = r"[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:/[+-]?\d+)?"


def numeric(value):
    text = str(value).strip().removeprefix("$").strip()
    if not re.fullmatch(NUMBER, text):
        raise ValueError(f"Invalid numeric answer: {value!r}")
    try:
        return Fraction(text.replace(",", ""))
    except (ZeroDivisionError, ValueError) as error:
        raise ValueError(f"Invalid numeric answer: {value!r}") from error


def extract_answer(text):
    if "####" not in text:
        return None
    try:
        return str(numeric(text.rsplit("####", 1)[1].strip()))
    except ValueError:
        return None


def arithmetic(expression):
    if not isinstance(expression, str) or len(expression) > 256:
        raise ValueError("Arithmetic expression is missing or too long")
    try:
        source = expression.strip().replace("×", "*").replace("÷", "/")
        tree = ast.parse(source, mode="eval")
        if sum(1 for _ in ast.walk(tree)) > 64:
            raise ValueError("Arithmetic expression is too complex")

        def evaluate(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                literal = ast.get_source_segment(source, node)
                if not re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)", literal):
                    raise ValueError("Use plain integer or decimal literals")
                value = Fraction(literal)
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = evaluate(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
            elif isinstance(node, ast.BinOp):
                left, right = evaluate(node.left), evaluate(node.right)
                if isinstance(node.op, ast.Add):
                    value = left + right
                elif isinstance(node.op, ast.Sub):
                    value = left - right
                elif isinstance(node.op, ast.Mult):
                    value = left * right
                elif isinstance(node.op, ast.Div):
                    value = left / right
                else:
                    raise ValueError("Only +, -, *, / and parentheses are allowed")
            else:
                raise ValueError("Only numeric arithmetic is allowed")
            if abs(value) > 10**15:
                raise ValueError("Arithmetic magnitude exceeds the validation limit")
            return value

        return evaluate(tree.body)
    except (SyntaxError, ZeroDivisionError, OverflowError, TypeError) as error:
        raise ValueError("Invalid arithmetic expression") from error


def equation_signature(equation):
    if not isinstance(equation, str) or equation.count("=") != 1:
        raise ValueError("Each equation must contain exactly one =")
    left, right = equation.split("=")
    value = arithmetic(left)
    if value != arithmetic(right):
        raise ValueError(f"Incorrect equation: {equation}")
    # shortcut: require the original operator structure; manually review equivalent rearrangements before extending this validator.
    source = left.strip().replace("×", "*").replace("÷", "/")
    tree = ast.parse(source, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            node.value = str(arithmetic(ast.get_source_segment(source, node)))
    signature = ast.dump(tree, include_attributes=False)
    return signature, str(value)


def make_splits(rows, counts, seed):
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Dataset IDs must be unique")
    if any(type(n) is not int or n <= 0 for n in counts.values()) or sum(counts.values()) > len(rows):
        raise ValueError("Split sizes must be positive and fit in the training pool")
    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    result, offset = {}, 0
    for name, count in counts.items():
        result[name] = shuffled[offset:offset + count]
        offset += count
    return result


def data_identity(manifest):
    keys = ("model", "model_revision", "dataset", "dataset_revision", "dataset_config", "seed", "sizes", "ids", "files")
    return {key: manifest[key] for key in keys}


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as source:
        for number, line in enumerate(source, 1):
            if line.strip():
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError("Expected a JSON object")
                    rows.append(row)
                except (json.JSONDecodeError, ValueError) as error:
                    raise ValueError(f"{path}, line {number}: {error}") from error
    return rows


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as destination:
        for row in rows:
            destination.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as destination:
        json.dump(data, destination, ensure_ascii=False, indent=2, allow_nan=False)
        destination.write("\n")


def validate_candidate(candidate, problem):
    try:
        if candidate["id"] != problem["id"] or candidate["pool"] not in POOLS:
            raise ValueError("Unknown question or language pool")
        if type(candidate["candidate"]) is not int or candidate["candidate"] < 0:
            raise ValueError("Candidate index must be a nonnegative integer")
        if numeric(candidate["answer"]) != numeric(problem["answer"]):
            raise ValueError("Candidate changed the final answer")
        steps = candidate["steps"]
        if not isinstance(steps, list) or not steps:
            raise ValueError("Candidate needs calculation steps")
        actual = []
        for step in steps:
            if not isinstance(step["text"], str) or any(token in step["text"] for token in ("####", "<|", "<think", "</think")):
                raise ValueError("Step text contains an answer marker or chat control token")
            if candidate["pool"] == "english" and re.search(r"[\u3400-\u9fff]", step["text"]):
                raise ValueError("English pool contains Chinese text")
            actual.append(equation_signature(step["equation"]))
        original = re.findall(r"<<([^<>]+)>>", problem["solution"])
        if not original or Counter(actual) != Counter(equation_signature(eq) for eq in original):
            raise ValueError("Candidate must preserve every original annotated calculation")
        return []
    except (KeyError, ValueError, TypeError) as error:
        return [str(error)]


def render_solution(candidate):
    steps = "\n".join(f"{s['text'].strip()} {s['equation']}".strip() for s in candidate["steps"])
    return f"{steps}\n#### {candidate['answer']}"


def feedback_prefix(candidate):
    steps = candidate["steps"][:len(candidate["steps"]) // 2]
    if not steps:
        raise ValueError("Feedback needs at least two steps so the final step can be withheld")
    answer = numeric(candidate["answer"])
    if any(arithmetic(s["equation"].split("=")[1]) == answer for s in steps):
        raise ValueError("Partial solution reveals the final answer")
    text = "\n".join(f"{s['text'].strip()} {s['equation']}".strip() for s in steps) + "\n"
    if "####" in text or re.search(rf"(?<![\d.]){re.escape(str(answer))}(?![\d.])", " ".join(s["text"] for s in steps)):
        raise ValueError("Partial solution text may reveal the final answer")
    return text


def select_conditions(problems, candidates, per_pool, penalty):
    if per_pool < 1 or not math.isfinite(penalty) or penalty < 0:
        raise ValueError("Candidate count and length penalty are invalid")
    lookup = {p["id"]: p for p in problems}
    groups, seen = defaultdict(lambda: defaultdict(list)), set()
    for candidate in candidates:
        key = (candidate["id"], candidate["pool"], candidate["candidate"])
        if key in seen or key[0] not in lookup or key[1] not in POOLS or type(key[2]) is not int or not 0 <= key[2] < per_pool:
            raise ValueError(f"Unknown or duplicate candidate: {key}")
        seen.add(key)
        if not validate_candidate(candidate, lookup[key[0]]):
            accuracy, tokens = candidate.get("feedback_accuracy"), candidate.get("tokens")
            if not isinstance(accuracy, (int, float)) or not math.isfinite(accuracy) or not 0 <= accuracy <= 1:
                raise ValueError(f"Candidate has no valid feedback score: {key}")
            if type(tokens) is not int or tokens <= 0:
                raise ValueError(f"Candidate has no positive tokenizer count: {key}")
        groups[key[0]][key[1]].append(candidate)
    result = {name: [] for name in CONDITIONS}
    excluded = []
    for problem in problems:
        pools = groups[problem["id"]]
        valid = {pool: [c for c in pools[pool] if not validate_candidate(c, problem) and not c.get("feedback_error")] for pool in POOLS}
        if any(len(pools[pool]) != per_pool or not valid[pool] for pool in POOLS):
            excluded.append({"id": problem["id"], "reason": "Missing candidate pool or no valid candidate in a pool"})
            continue
        result["original"].append(dict(problem, reviewed=True))
        for pool in POOLS:
            shortest = min(valid[pool], key=lambda c: (c["tokens"], c["candidate"]))
            longest = max(c["tokens"] for c in valid[pool])
            feedback = min(valid[pool], key=lambda c: (-(c["feedback_accuracy"] - penalty * c["tokens"] / longest), c["tokens"], c["candidate"]))
            for strategy, chosen in (("shortest", shortest), ("feedback", feedback)):
                chosen = dict(chosen, answer=problem["answer"])
                result[f"{pool}-{strategy}"].append(dict(problem, **{k: v for k, v in chosen.items() if k != "solution"}, solution=render_solution(chosen)))
    return result, excluded


def mask_training_tokens(prompt, full, max_length):
    if len(full) > max_length:
        raise ValueError(f"Training example has {len(full)} tokens, exceeding max_length={max_length}; increase it for every condition")
    if full[:len(prompt)] != prompt or len(full) <= len(prompt):
        raise ValueError("Assistant template does not extend the generation prompt")
    return {"input_ids": full, "attention_mask": [1] * len(full), "labels": [-100] * len(prompt) + full[len(prompt):]}


def summarize(rows):
    if not rows:
        raise ValueError("Cannot summarize an empty evaluation")
    tokens = [r["output_tokens"] for r in rows if r["output_tokens"] is not None]
    return {"sample_size": len(rows), "correct": sum(bool(r["correct"]) for r in rows),
            "accuracy": sum(bool(r["correct"]) for r in rows) / len(rows),
            "mean_output_tokens": statistics.mean(tokens) if tokens else None, "token_measurements": len(tokens),
            "mean_seconds": statistics.mean(r["seconds"] for r in rows),
            "failures": sum(bool(r.get("error")) for r in rows),
            "truncated": sum(bool(r.get("truncated")) for r in rows)}


def paired_comparison(reference, candidate, seed):
    left, right = {r["id"]: r for r in reference}, {r["id"]: r for r in candidate}
    if not left or set(left) != set(right) or len(left) != len(reference) or len(right) != len(candidate):
        raise ValueError("Paired comparison needs identical, unique question IDs")
    ids = sorted(left)
    differences = [int(right[i]["correct"]) - int(left[i]["correct"]) for i in ids]
    rng = random.Random(seed)
    bootstrap = sorted(statistics.mean(rng.choices(differences, k=len(ids))) for _ in range(2000))
    measurable = all(r.get("output_tokens") is not None and not r.get("error") for r in [*reference, *candidate])
    old_tokens = sum(left[i]["output_tokens"] for i in ids) if measurable else 0
    return {"sample_size": len(ids), "accuracy_difference": statistics.mean(differences),
            "accuracy_difference_95_ci": [bootstrap[49], bootstrap[1949]],
            "token_reduction": 1 - sum(right[i]["output_tokens"] for i in ids) / old_tokens if old_tokens else None,
            "bootstrap_samples": 2000, "seed": seed}
