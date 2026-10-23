# Research pipeline implementation plan

**Goal:** Make this repository ready to run the compact multilingual reasoning pilot described in `final-project-proposal.md`.

**Architecture:** A small Python command-line package under `research/`, separate from the existing public explainer. Local datasets, model caches, adapters and results live under ignored directories. Preparation, rewriting, scoring, selection, training and evaluation are separate commands so expensive work is explicit.

**Tech stack:** Python 3.12, CUDA PyTorch, Transformers, Datasets, PEFT, Accelerate; standard-library unittest and JSON/JSONL artifacts.

**Scope and decisions:** Implement the previously described pipeline directly in this checkout, as requested. Start with Qwen3-0.6B and 100 training questions, with independent calibration/development partitions. Use ordinary visible assistant solutions with Qwen thinking disabled consistently. LoRA updates only adapters. No hosted API calls, paid jobs, publication or full experiment runs are part of setup.

## Tasks

- [x] Write and run failing tests for exact answer parsing, safe arithmetic, disjoint splits, candidate validation, matched selection, leakage-free prefixes, answer-only training labels and failure-inclusive metrics.
- [x] Implement `research/core.py` with those pure data operations.
- [x] Implement `research/runtime.py` and `research/__main__.py`: doctor, prepare, rewrite/import, score, select, train, evaluate and compare. Save model/data revisions, configuration, seeds, IDs, environment and per-question outputs.
- [x] Add `configs/pilot.json`, pinned dependencies, local PowerShell setup, ignore rules and root README with runnable commands and teacher/review workflow.
- [x] Install the local environment, cache the starting model/dataset, run all unit tests and existing site checks, then exercise GPU inference and a short LoRA training/reload smoke check.

## Review focus

- Malformed numbers, unsafe arithmetic and invalid rewrites fail closed.
- A question and its rewrites never cross splits; final test evaluation requires an explicit opt-in.
- Invalid question bundles are excluded from every comparison condition.
- Missing, truncated and failed answers remain in the evaluation denominator.
- Existing results and adapters cannot be overwritten accidentally; source credentials and local artifacts stay outside public site assets and Git.

Full training, bulk teacher generation, human semantic review, calibration of the feedback penalty, transfer-set design and final test evaluation remain research work after setup. A smoke check is labelled as such and is not a scientific result.

## Implementation and review record

- User clarified that teammate-readable context, instructions and reproduction are part of this repository. Added `AGENTS.md`, `docs/TEAM_GUIDE.md`, `docs/EXPERIMENT_LOG.md`, complete dependency constraints and a versioned pilot data identity. These do not depend on local Codex skills or chat history.
- Independent read-only review identified mismatched adapter training populations and final-test CLI overrides. Added failing tests, then guards for matched training IDs/settings, planned budgets and full official-test evaluation.
- Review also caught decimal rounding in arithmetic validation. A regression test failed before changing the validator to parse original numeric literals as exact fractions.
- Additional tests reject interrupted comparisons and keep missing token measurements distinct from zero. Data identity excludes machine-specific metadata; split files use LF for cross-platform hashes.
- Offline suite: 27 tests passed after these changes. Existing explainer suite: 5 tests passed. GPU installation confirmed CUDA availability; live inference/training verification is recorded separately when complete.
- GPU verification completed: three base-model predictions, two LoRA optimizer steps, adapter save/reload, three adapter predictions and a paired report. Exact commands, environment and limits are in `docs/SETUP_VERIFICATION.md`. This completes setup, not the research experiment.
