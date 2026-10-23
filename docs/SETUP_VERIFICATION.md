# Setup verification: 24 October 2026

This records infrastructure checks completed on the original Windows laptop. It is not a result of the proposed research experiment. Read the [team guide](TEAM_GUIDE.md) and [README](../README.md) to reproduce the setup on another machine.

## Verified environment

- Python 3.12.10, Windows 11.
- NVIDIA GeForce RTX 4060 Laptop GPU, 8,585,216,000 bytes reported VRAM.
- PyTorch 2.8.0+cu128; CUDA 12.8 available.
- Transformers 4.57.3, Datasets 4.4.1, PEFT 0.18.0, Accelerate 1.12.0.
- Complete package constraints: `requirements-lock.txt`. `pip check` reported no broken requirements.
- Student commit: `Qwen/Qwen3-0.6B@c1899de289a04d12100db370d81485cdf75e47ca`.
- Dataset commit: `openai/gsm8k@740312add88f781978c0658806c59bc2815b9866`, configuration `main`.

The source was uncommitted during these checks, based on Git commit `9752f65ac0ec2e55b726b734023cb13a82e4d6cf` with `git_dirty: true`. To reproduce the setup, use the Git commit that adds this document, which includes the checked source snapshot; that older base commit alone does not contain this pipeline.

## Completed checks

| Check | Command / evidence | Outcome |
|---|---|---|
| Isolated environment | `scripts/setup.ps1`, then `python -m research doctor` inside `.venv` | Dependencies installed locally; CUDA detected |
| Dependency compatibility | `.venv/Scripts/python.exe -m pip check` | No broken requirements |
| Data preparation | `research prepare` | 100 train, 300 calibration, 200 development; unique saved IDs from the training pool |
| Data reproduction identity | Compare `data_identity(artifacts/data/pilot/manifest.json)` with `configs/pilot-data-lock.json` | Exact match of revisions, IDs and split hashes |
| Python tests | `.venv/Scripts/python.exe -m unittest discover -s tests -v` | 27 tests passed |
| Existing explainer tests | `npm --prefix explainer run check` | 5 tests passed |
| GPU inference | `research evaluate --budget 128 --limit 3 --output artifacts/runs/smoke-unchanged` | Three development predictions saved; zero runtime failures |
| LoRA training and save | `research train --condition original --smoke-steps 2 --output artifacts/runs/smoke-original` | Two optimizer steps completed; adapter saved |
| Adapter reload and inference | `research evaluate --adapter artifacts/runs/smoke-original/adapter --budget 128 --limit 3 --output artifacts/runs/smoke-adapter` | Adapter reloaded; three predictions saved; zero runtime failures |
| Paired report | `research compare --reference artifacts/runs/smoke-unchanged --candidate artifacts/runs/smoke-adapter --output artifacts/runs/smoke-comparison.json` | Comparison report generated on matching questions/settings |
| Artifact isolation | `git check-ignore` for `.venv`, model cache, prepared data, adapter weights and `.env` | All matched ignore rules |

Commands beginning with `research` in the table use `.venv/Scripts/python.exe -m research` from the repository root. The original prepared training partition contains 100 examples, but the training smoke check performed only **two updates**, not the full pilot training.

The training check used 5,046,272 trainable adapter parameters. Its maximum prepared sequence was 388 tokens. Trainer reported 24.9217 seconds of training time; training plus saving took about 26.8 seconds, excluding model loading. Peak PyTorch-allocated VRAM was 1,849,539,072 bytes, which does not include all driver or other applications' GPU memory.

Smoke predictions, model outputs, metadata and the adapter are in ignored `artifacts/runs/smoke-*` directories on the setup machine. They are not carried by Git and were not copied into the public website. The three-question accuracy values must not be used as study findings.

## Review and limitations

An independent code review identified gaps in matching adapter training populations, final-test CLI overrides and decimal precision. Regression tests reproduced these issues before fixes. Comparisons now check matched training question IDs/settings, final testing rejects sample limits and unplanned budgets, and arithmetic uses exact source numeric literals.

The graph index predates the new pipeline, so source inspection and executable tests were used for its verification. Offline tests cover parsing, safe arithmetic, disjoint splits, candidate checks, answer leakage guards, matched condition selection, failure-inclusive metrics, prompt masking, incomplete comparisons and final-test gates.

Not executed during setup: live teacher/Ollama generation, human semantic review, bulk feedback scoring, calibrated candidate selection, full original-solution training, five-condition experiments, 1.7B profiling, independent transfer evaluation, repeated training seeds, or official-test evaluation. Linux instructions are provided but have not been verified on a Linux GPU host.

No hosted API spending, cloud GPU rental, public deployment or Git push was performed as part of setup. Update [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md) when research work begins.
