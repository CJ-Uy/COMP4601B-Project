# Original-solution pilot: 24 October 2026

**Status: original-solution training complete; development evaluation in progress.** This is the 100-training-question feasibility baseline, evaluated using separate development questions. It does not establish the multilingual method's performance.

## Reproduction

- Source: `ab2747cbad821a739e47a69c34463d33b2336e9a`.
- Configuration: `configs/pilot.json`, unchanged for this run.
- Inputs: `artifacts/data/pilot/`; exact revisions, IDs and split hashes are versioned in `configs/pilot-data-lock.json`.
- Student: Qwen3-0.6B, pinned model commit `c1899de289a04d12100db370d81485cdf75e47ca`.
- Task: GSM8K, pinned dataset commit `740312add88f781978c0658806c59bc2815b9866`.
- Split audit: 100 train, 300 calibration and 200 development questions; no shared IDs; all split file hashes and gold final-answer parsing verified.
- Training: three epochs; seed 42; LoRA rank 8, alpha 16 and dropout 0.05; learning rate 0.0002; batch size 1; accumulation 8; maximum sequence length 1024; gradient checkpointing.
- Evaluation: the first 50 saved development questions, with the same decoding settings for both models; visible reasoning budget 256 followed by up to 64 answer tokens. The user explicitly selected this quick scope; the full 200-question, three-budget sweep is deferred. Built-in Qwen thinking is disabled. The official test set is not used.
- Hardware: RTX 4060 Laptop GPU, 8 GB VRAM. Observed on AC power with Legion Performance Mode. Python and package versions are in each run's metadata and `requirements-lock.txt`.

Commands, run sequentially from the repository root:

```powershell
.venv\Scripts\python.exe -m research train --condition original --output artifacts/runs/pilot-original
.venv\Scripts\python.exe -m research evaluate --budget 256 --limit 50 --output artifacts/runs/pilot-quick-unchanged
.venv\Scripts\python.exe -m research evaluate --adapter artifacts/runs/pilot-original/adapter --budget 256 --limit 50 --output artifacts/runs/pilot-quick-original-eval
.venv\Scripts\python.exe -m research compare --reference artifacts/runs/pilot-quick-unchanged --candidate artifacts/runs/pilot-quick-original-eval --output artifacts/runs/pilot-quick-baseline-comparison.json
```

Use new output names when reproducing; completed or interrupted directories are preserved.

An earlier full-sweep attempt in `artifacts/runs/pilot-unchanged/` was interrupted after 29 predictions at budget 128 to investigate throughput. Its `INTERRUPTED.json` marks it incomplete and excluded from the primary comparison. A separate three-question diagnostic compared one versus 24 PyTorch CPU threads: identical generated outputs, mean 10.668 versus 6.008 seconds after warm-up. The default 24 threads was retained. Diagnostic timings are not the development result; no training or evaluation code/configuration was changed.

## Measurements

Training completed all three epochs and 39 optimizer updates. The final adapter is saved in `artifacts/runs/pilot-original/adapter/`; the completed `run.json` confirms `smoke_check: false` and 100 training IDs.

| Training measurement | Observed value |
|---|---:|
| Trainer runtime | 188.1652 seconds |
| Training plus adapter save, excluding model loading | 190.6030 seconds |
| Mean training loss | 0.5506046 |
| Peak PyTorch-allocated VRAM | 2,032,115,712 bytes |
| Maximum prepared training sequence | 388 tokens |
| Trainable adapter parameters | 5,046,272 |

These are compute and training observations, not evidence of improved held-out accuracy. Development measurements are pending. Each evaluation retains predictions incrementally and writes `summary.json` only on completion. Do not interpret partial files as completed results.

The unchanged reference has completed all 50 development questions: 18 correct (36%), mean 128.38 generated tokens and 13.8091 seconds per question, zero runtime failures, one truncated output and 19 unparseable final answers. The adapter evaluation is still running; the paired comparison is pending.

Accuracy here requires a parseable numeric final answer after `####`; unparseable responses count as incorrect. This combines arithmetic success and output-format compliance. For example, the unchanged response for `train-5875` ends with `#### 29 pages in Lana's binder after adding Duane's.` while the gold answer is `29`; the extra text makes it unparseable under the fixed parser. Do not describe a later improvement in this metric as a pure improvement in arithmetic reasoning. The parser has not been changed after observing these outputs.

## Interpretation limits

- This original-solution adapter tests ordinary fine-tuning feasibility; no rewritten examples or teacher output are used.
- Development measurements guide the pilot. They are not final-test results and should not be presented as such.
- A single training seed does not establish run-to-run stability. Token and accuracy changes must be considered together, including failure/truncation counts.
- If later rewrite preparation excludes any questions, retrain the original baseline on the same retained IDs before making the five-condition comparison.
- Raw artifacts, models and adapters remain local and ignored by Git. Share an archive separately to reproduce exact outputs; the report preserves the procedure and completed aggregate observations.
