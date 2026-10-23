# Experiment and decision log

Keep this file in Git so both researchers can see why the current settings were chosen. Preserve earlier entries and identify superseded decisions explicitly. Put bulk outputs in the ignored artifact archive, not in this document.

## 24 October 2026: repository setup

- Added the Python experiment pipeline, pilot config, local environment setup, tests and teammate documentation alongside the existing explainer.
- Starting settings follow the final proposal; default hyperparameters and the length penalty remain provisional.
- Setup verification is recorded in [SETUP_VERIFICATION.md](SETUP_VERIFICATION.md). Smoke checks are infrastructure checks, not evidence for multilingual compression.
- No teacher has been selected by setup, no human semantic review has been claimed, and no full five-condition or final-test result has been established.
- Next research action: run and profile the original-solution pilot baseline, then choose the student/teacher and test a small rewrite batch.

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
