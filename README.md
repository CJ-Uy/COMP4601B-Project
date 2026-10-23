# Compact multilingual reasoning

COMP 4901B research project: can a small language model learn shorter arithmetic solutions without losing answer accuracy? The study compares original GSM8K solutions with compact English and English–Mandarin solutions, using either shortest-candidate selection or feedback from the unchanged student model.

The [final proposal](final-project-proposal.md) describes the study. This repository contains both the experiment pipeline and the [public explainer](explainer/README.md).

**Joining the project?** Read the [team guide and project context](docs/TEAM_GUIDE.md), then follow the setup below. Record research decisions in the [experiment log](docs/EXPERIMENT_LOG.md). Coding assistants should also read [AGENTS.md](AGENTS.md).

## Start on this Windows laptop

These are fresh-checkout instructions. The original setup machine already has the environment and prepared pilot; see [setup verification](docs/SETUP_VERIFICATION.md). Keep that data directory and use new names for new runs.

Python 3.12 and an NVIDIA GPU are expected. The setup installs CUDA PyTorch and the research packages inside this repository's `.venv`; it does not change global Python packages. Downloads need an internet connection and several GB of free disk space.

To read the code and run its offline tests only, Python 3.12 is sufficient: `python -m unittest discover -s tests -v`. Model downloads and the GPU environment are needed for actual experiments.

Run from the repository root in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1
.venv\Scripts\python.exe -m research prepare
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`prepare` downloads Qwen3-0.6B and GSM8K, resolves their current revisions to immutable commit IDs, and saves 100 training, 300 calibration and 200 development questions. All partitions come from GSM8K's training pool. It records their original IDs, hashes and seed. Official test examples are not used in preparation.

The supplied config already pins the exact model and dataset commits verified during setup. [configs/pilot-data-lock.json](configs/pilot-data-lock.json) records the pilot's expected question IDs and split hashes. Files use UTF-8 and LF line endings so those hashes can be checked across operating systems.

The supplied pilot configuration is [configs/pilot.json](configs/pilot.json). To change it, copy the file and place `--config path/to/config.json` **before** the subcommand. A different student model needs a separate prepared-data directory. The 100 pilot questions are the first 100 questions of the seeded training partition; increasing `splits.train` to 1000 keeps them in training but moves the later partitions, so prepare the expanded study in a new directory and do not mix its runs with pilot runs.

```powershell
.venv\Scripts\python.exe -m research doctor
.venv\Scripts\python.exe -m research --help
.venv\Scripts\python.exe -m research train --help
```

Linux can use Python 3.12, `python -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, and the same module commands. The pinned PyTorch build requires a compatible NVIDIA driver; `doctor` reports CUDA availability. Native Windows is the setup verified here.

## Run the original-solution baseline

First check a few development questions and a short training run:

```powershell
.venv\Scripts\python.exe -m research evaluate --budget 128 --limit 3 --output artifacts/runs/smoke-unchanged
.venv\Scripts\python.exe -m research train --condition original --smoke-steps 2 --output artifacts/runs/smoke-original
.venv\Scripts\python.exe -m research evaluate --adapter artifacts/runs/smoke-original/adapter --budget 128 --limit 3 --output artifacts/runs/smoke-adapter
```

Smoke adapters are labelled in their metadata and cannot be used for official test evaluation. These short runs verify the pipeline; they do not measure whether the research idea works.

For the full pilot baseline, omit `--smoke-steps` and the evaluation limits:

```powershell
.venv\Scripts\python.exe -m research evaluate --output artifacts/runs/pilot-unchanged
.venv\Scripts\python.exe -m research train --condition original --output artifacts/runs/pilot-original
.venv\Scripts\python.exe -m research evaluate --adapter artifacts/runs/pilot-original/adapter --output artifacts/runs/pilot-original-eval
.venv\Scripts\python.exe -m research compare --reference artifacts/runs/pilot-unchanged --candidate artifacts/runs/pilot-original-eval --output artifacts/runs/pilot-baseline-comparison.json
```

Outputs use new directories and files. Existing work is never overwritten; choose a new run name for another attempt. Interrupted runs retain the artifacts already written; evaluation has flushed per-question predictions, training has its request metadata, and rewrite generation has raw teacher responses. Restart in a new output directory; automatic resumption is not implemented.

## Prepare rewritten solutions

Choose and fix one teacher after the pilot. Hosted-model access is optional: the code makes no paid API calls and stores no API keys. It supports importing teacher JSONL or using an already running local Ollama installation.

To use the proposal's local fallback, install Ollama separately, pull `qwen3:8b`, and run:

```powershell
.venv\Scripts\python.exe -m research rewrite --ollama-model qwen3:8b --output artifacts/rewrites/train
```

This produces four English and four multilingual candidates per problem, so the 100-question pilot requests **800 teacher completions**. Start with `--limit 2` and a different output directory to inspect quality and teacher memory use. The student and teacher run in separate commands. A quantized teacher has its own memory requirements; the student GPU smoke check does not establish that the teacher fits.

For a hosted teacher or manually prepared data, import a UTF-8 JSONL file. Each line has this shape (an illustrative problem, not an actual prepared question):

```json
{"id":"train-123","pool":"english","candidate":0,"steps":[{"text":"Items","equation":"3*5=15"},{"text":"Total","equation":"15+2=17"}],"answer":"17","reviewed":false}
```

Use IDs, questions and original solutions from `artifacts/data/pilot/train.jsonl`; `pool` is `english` or `multilingual`, and candidate indices are 0–3 in each pool. Preserve one equation per original `<<expression=result>>` calculation. Ask the teacher for alternative compact explanations with unchanged equations and final answer. Keep exact teacher version, prompts, raw outputs and usage costs with your source file.

```powershell
.venv\Scripts\python.exe -m research rewrite --import-file my-teacher-candidates.jsonl --teacher-label "Exact teacher version; prompt version; provenance file" --output artifacts/rewrites/train
```

The validator checks numeric answers, safe arithmetic, preservation of the original calculation structures, and the English pool's absence of Chinese characters. It deliberately rejects algebraically rearranged expressions, added calculations and missing steps. It **cannot prove unchanged meaning**, English fluency or that a multilingual candidate actually uses Mandarin. Inspect validation errors, review selected solutions against their original questions, and set `reviewed` to the JSON boolean `true` only after human review. For early screening, training accepts the explicit `--allow-unreviewed` flag and labels the run accordingly; screening adapters cannot be used for final testing.

## Score, select and train the five conditions

```powershell
.venv\Scripts\python.exe -m research score --candidates artifacts/rewrites/train/candidates.jsonl --output artifacts/scores/train
.venv\Scripts\python.exe -m research select --scored artifacts/scores/train/scored.jsonl --output artifacts/conditions/pilot
```

The scorer counts candidate tokens with the **student tokenizer**. It shows the unchanged student the first half of each candidate's steps and samples two completions. Prefixes that reveal the final answer, or have no intermediate step, are rejected. It saves every sampled completion and seed.

Selection maximizes `feedback_accuracy - length_penalty * tokens / longest_valid_candidate_tokens_in_that_question_and_pool`. The default penalty `0.1` is **provisional**. Generate and score a separate calibration set using `rewrite --split calibration` and `score --split calibration`; use those results to choose the penalty and document the decision before training the final comparisons. Recheck a subset with `score --attempts 8` to assess ranking stability. Calibration examples never train adapters. Penalty choice and stability interpretation remain research decisions; the software does not claim to have calibrated them.

The selected files contain exactly the same question IDs across all five conditions. A question lacking a complete candidate pool or any usable candidate in either pool is removed from every condition, including the original baseline. Review selected rewritten files, then train each condition:

```powershell
$conditions = 'original', 'english-shortest', 'english-feedback', 'multilingual-shortest', 'multilingual-feedback'
foreach ($condition in $conditions) {
    .venv\Scripts\python.exe -m research train --conditions artifacts/conditions/pilot --condition $condition --output "artifacts/runs/matched-$condition"
    if ($LASTEXITCODE -ne 0) { throw "Training failed: $condition" }
}
```

For comparisons across these five conditions, use this **matched original baseline**, since its IDs reflect any bundle exclusions. The earlier standalone baseline establishes feasibility on the original pilot set.

Training uses LoRA, batch size 1, gradient accumulation 8 and gradient checkpointing. It freezes the base model and learns adapters. Loss covers assistant solution tokens and the end token; question/prompt and padding tokens are masked. Overlong examples fail explicitly instead of silently dropping the answer. Choose a shared maximum length that fits every condition.

## Evaluate and freeze settings

Evaluation supplies only the question. Qwen's built-in thinking mode is disabled consistently; the experiment trains and measures visible written solutions. Each run uses reasoning budgets of 128, 256 and 512 tokens, followed by up to 64 answer tokens. Reasoning stops at `####` when the model emits it; otherwise the evaluator inserts the answer marker after the reasoning stage. Inserted tokens are recorded separately and are not counted as generated tokens.

All predictions are retained, including incorrect, unparseable, truncated and failed answers. Correctness requires an explicit numeric final answer, with exact rational-number comparison. Accuracy includes failures. A failure with unavailable token counts records `null`; summaries show how many token measurements exist, and comparisons with failures do not report a token-reduction claim. Runtime includes both generation stages and CUDA synchronization. Compare timing under the same laptop power/thermal settings; timing is not a direct energy measurement.

```powershell
.venv\Scripts\python.exe -m research evaluate --adapter artifacts/runs/matched-multilingual-feedback/adapter --output artifacts/runs/multilingual-feedback-development
.venv\Scripts\python.exe -m research freeze --output artifacts/frozen-settings.json
```

Only after choosing settings on development data and recording the decision, evaluate the untouched official test set:

```powershell
.venv\Scripts\python.exe -m research evaluate --adapter artifacts/runs/matched-multilingual-feedback/adapter --split official-test --final-test --frozen-settings artifacts/frozen-settings.json --output artifacts/runs/multilingual-feedback-test
```

Repeat with each comparator and identical settings. `compare` requires matched evaluation settings and question IDs, and returns the accuracy difference with a paired 2,000-sample bootstrap 95% interval and observed token reduction. This interval is over questions in one pair of runs; it does not replace repeated training seeds. Keep the same prepared split directory when changing the training seed.

The independent transfer set, human review of 50 outputs, repeated training seeds, calibration decisions and final report remain research work. No transfer-set results or multilingual advantage are fabricated by setup.

## Repository layout and reproducibility

| Path | Purpose |
|---|---|
| `research/` | Data checks, CLI, generation, LoRA training and evaluation |
| `configs/pilot.json` | Proposed pilot settings |
| `scripts/setup.ps1` | Local Windows environment installation |
| `requirements.txt` | Pinned direct dependencies and CUDA wheel source |
| `tests/` | Offline correctness and CLI safety tests |
| `artifacts/data/` | Prepared split files and immutable revision manifest |
| `artifacts/runs/` | Local adapters, environment/config metadata and predictions |
| `.cache/huggingface/` | Downloaded model and dataset cache |
| `explainer/` | Existing website; deploys only `explainer/public/` |

Local environments, caches, experiment artifacts and `.env` files are ignored by Git. Archive `artifacts/` separately for reproducibility; ignored does not mean backed up. Manifests record direct package versions, Python, GPU, Git commit/dirty status, seeds, configurations and model/dataset revisions. `requirements-lock.txt` records the complete environment tested during setup.

To check a fresh preparation against the versioned pilot identity:

```powershell
.venv\Scripts\python.exe -c "import json; from pathlib import Path; from research.core import data_identity; actual=json.loads(Path('artifacts/data/pilot/manifest.json').read_text(encoding='utf-8')); expected=json.loads(Path('configs/pilot-data-lock.json').read_text(encoding='utf-8')); assert data_identity(actual)==expected, 'Pilot data differs'; print('Pilot data matches')"
```

Run both test suites before changing the public site or research code:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
npm --prefix explainer run check
```

Measured research results are not published automatically. Add only reviewed scientific results to the explainer following its README. Setup and smoke measurements are local verification evidence.

## Sources and attribution

- [Qwen3-0.6B model and usage](https://huggingface.co/Qwen/Qwen3-0.6B), Apache 2.0.
- [GSM8K dataset](https://huggingface.co/datasets/openai/gsm8k), MIT.
- [PyTorch installation](https://pytorch.org/get-started/locally/), [Transformers](https://huggingface.co/docs/transformers/v4.57.3/en/index), [PEFT LoRA](https://huggingface.co/docs/peft/v0.18.0/en/package_reference/lora).
