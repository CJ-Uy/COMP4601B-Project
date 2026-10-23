# Experiment and decision log

Keep this file in Git so both researchers can see why the current settings were chosen. Preserve earlier entries and identify superseded decisions explicitly. Put bulk outputs in the ignored artifact archive, not in this document.

## 24 October 2026: repository setup

- Added the Python experiment pipeline, pilot config, local environment setup, tests and teammate documentation alongside the existing explainer.
- Starting settings follow the final proposal; default hyperparameters and the length penalty remain provisional.
- Setup verification is recorded in [SETUP_VERIFICATION.md](SETUP_VERIFICATION.md). Smoke checks are infrastructure checks, not evidence for multilingual compression.
- No teacher has been selected by setup, no human semantic review has been claimed, and no full five-condition or final-test result has been established.
- Next research action: run and profile the original-solution pilot baseline, then choose the student/teacher and test a small rewrite batch.

## 24 October 2026: original-solution pilot started

- User authorized the 100-question pilot and full original-solution baseline training.
- Source snapshot: `ab2747cbad821a739e47a69c34463d33b2336e9a`; no changes to the training code or pilot configuration for this run.
- Prepared input identity matches `configs/pilot-data-lock.json`. Audited 100 training, 300 calibration and 200 development IDs: all disjoint, split hashes verified, and all gold final answers parse correctly.
- Training uses the original supplied solutions, seed 42, three epochs, LoRA rank 8, batch size 1 and accumulation 8. Output: `artifacts/runs/pilot-original/`.
- Initial plan: unchanged Qwen3-0.6B versus the original-solution adapter on all 200 development questions at reasoning budgets 128, 256 and 512. Superseded for this run by the user's explicit quick scope: the first 50 saved development questions, budget 256 plus up to 64 answer tokens. The full sweep is deferred; official test examples remain reserved.
- Laptop observed on AC power with Legion Performance Mode; sampled hardware readings are retained in the training artifact directory. Timing remains specific to this hardware and its operating conditions.
- Teacher decision: the user wants GPT-6.1 versus Opus 5.5 generating rewritten training solutions, with outputs imported from their ChatGPT and Claude accounts. The shared ten-question [protocol and prompt pack](TEACHER_COMPARISON.md) keep the datasets separate. Later teacher-specific student adapters must use matched IDs/settings. No teacher output was used in the original baseline, and no hosted teacher calls were made.
- Training completed: three epochs, 39 optimizer updates, 188.1652 seconds of Trainer runtime, peak PyTorch-allocated VRAM 2,032,115,712 bytes. Final adapter and `run.json` are saved; this is a full pilot training run, not a smoke check.
- Development evaluation is in progress. Current status and completed measurements: [pilot report](pilots/2026-10-24-original-baseline.md). Evaluation results will be entered only after their artifacts confirm completion.
- Unchanged quick reference completed 50/50: 18 correct, mean 128.38 output tokens, zero runtime errors, one truncation and 19 unparseable final answers. The original adapter is now evaluating the same questions. Accuracy includes strict final-answer formatting; the pilot report records an example and this interpretation limit.
- Teacher handoff: the user will open the repository with Opus. Added a [shared repository-assistant instruction](../prompts/run-teacher-comparison.md), with only the output arm changed for a fresh GPT-6.1 session. Keep the same conversation-isolation procedure for both teachers; record any UI/backend settings that cannot be controlled as unknown. Prompt-pack hashes and first-ten locked training IDs were verified, and all 30 Python tests pass.

## 24 October 2026: Opus ten-question outputs checked

- User ran the repository prompt in Opus and asked for a completion check. Found all ten expected response files and the provenance record in `artifacts/teacher-comparison/chat-export-round1/opus55/`.
- Independent audit: 80 unique expected candidates, 40 per language pool, 80 arithmetic/structure passes, exact source equations in original order, unchanged final answers, prompt/input hashes verified and all `reviewed` flags false. Import into `artifacts/rewrites/teacher-opus55-round1/` completed successfully. No responses were rewritten or repaired during this check.
- Provenance records a single Claude Code conversation with reported Opus 5.5 label, custom session instructions, and unknown backend snapshot/seed/billing. GPT should use the same shared-conversation procedure; capture any differing session instructions.
- GPT raw response directory has no JSONL response files yet. Human meaning review, student feedback, token comparison and downstream training remain pending. The [screening report](pilots/2026-10-24-teacher-screening.md) records evidence and limits; raw data stays local and ignored.
- Static prefix eligibility accepts 72/80 candidates. All eight `train-3620` candidates correctly preserve a one-calculation source and therefore cannot supply an intermediate-only prefix under the current feedback policy. This check performs no student generations; GPT must follow the same eligibility rule.

## 24 October 2026: quick original-baseline comparison completed

- Both serial evaluations exited successfully with 50 predictions each, using budget 256 plus up to 64 answer tokens. Compared unchanged Qwen3-0.6B against the full 100-question original-solution adapter. No training/evaluation code or pilot configuration was changed.
- Strict formatted-answer accuracy: 18/50 (36%) versus 24/50 (48%). Paired difference +12 percentage points, question-bootstrap 95% interval −4 to +28 points; 2,000 bootstrap samples, seed 42. This does not establish an improvement across training seeds.
- Mean output tokens: 128.38 versus 115.24, a 10.24% reduction. Mean generation seconds: 13.8091 versus 21.3756, about 55% slower with the current unmerged-adapter runtime. Zero runtime errors and one truncated output in each arm.
- Unparseable final answers fell from 19 to one. Eight of the 12 newly correct outputs had unparseable reference answers, so the observed accuracy change cannot be described as a pure arithmetic-reasoning gain.
- Comparison and separate pairing/format audit: `artifacts/runs/pilot-quick-baseline-comparison.json` and `artifacts/runs/pilot-quick-baseline-audit.json`. Matching IDs, gold answers, seeds, prompt-token counts and full evaluation manifests were verified. The [pilot report](pilots/2026-10-24-original-baseline.md) contains the completed table and reproduction commands.
- The full 200-question/three-budget sweep, official test, additional training seeds, merged-adapter benchmarking, GPT teacher collection and teacher-specific training remain unrun. Raw artifacts remain local and ignored; the procedure and aggregate findings are tracked for the team.

## Copy for a research decision

```text
Date and researchers:
Question being decided:
Evidence / calibration or development run IDs:
Decision and reason:
Alternatives considered:
Configuration or protocol fields changed:
Previous decision superseded, if any:
Effect on existing runs and which comparisons need rerunning:
```

## Copy for a run or teammate handoff

```text
Date, researcher and run ID:
Purpose (smoke / screening / pilot / final):
Git commit and clean/dirty status; source snapshot if dirty:
Exact command from the repository root:
Config file and seed:
Prepared-data manifest, model revision and dataset revision:
Teacher version / prompt provenance, if relevant:
Inputs and artifact archive location (no credentials):
Outputs / adapter / predictions / summary location:
Hardware and relevant power/thermal settings:
Elapsed time, peak memory, teacher/GPU cost where applicable:
Observed result and failed/truncated/unparseable counts:
Human review performed, by whom, and remaining limitations:
Next action and owner:
```
