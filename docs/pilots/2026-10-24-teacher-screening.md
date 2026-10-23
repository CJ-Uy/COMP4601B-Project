# Teacher screening: 24 October 2026

**Status: Opus generation and structural validation complete; GPT generation pending.** This is the ten-training-question screening round, not a student-training result or a comparison winner.

## Opus output audit

| Check | Observed result |
|---|---:|
| Expected question response files present | 10 / 10 |
| Unique expected `(id, pool, candidate)` combinations | 80 / 80 |
| English candidates | 40 |
| Multilingual candidates | 40 |
| Arithmetic/structure validator passes | 80 / 80 |
| Exact annotated equations preserved in original order | 80 / 80 |
| Eligible for the current partial-solution prefix check | 72 / 80 |
| Marked human-reviewed | 0 |
| GPT response files in the corresponding raw directory | 0 |

Verified the input and ten prompt hashes against the prepared manifest, all expected candidate indices 0–3 in each pool, unchanged final numeric answers, and stable response-file hashes during the audit. The existing `research rewrite` importer independently accepted all 80 candidates. Arithmetic validity does not establish unchanged meaning; human semantic review remains pending.

A static call to `feedback_prefix` accepts 72 candidates. The eight candidates for `train-3620` have only one annotated calculation, as required by the supplied source, so the current policy cannot withhold a final step while retaining an intermediate step. This is a source/prefix constraint, not missing or invalid Opus output. Apply the same policy to GPT and use common eligible IDs for downstream comparisons. No student feedback generations were run by this check.

Local artifacts:

- Prompt/input manifest: `artifacts/teacher-comparison/chat-export-round1/manifest.json`.
- Opus first responses and provenance: `artifacts/teacher-comparison/chat-export-round1/opus55/`.
- Consolidated candidates: `artifacts/teacher-comparison/chat-export-round1/opus55/candidates.jsonl`.
- Audit with response hashes and validation results: `artifacts/teacher-comparison/chat-export-round1/opus55/validation-audit.json`.
- Static prefix eligibility: `artifacts/teacher-comparison/chat-export-round1/opus55/prefix-audit.json`.
- Imported candidates and run metadata: `artifacts/rewrites/teacher-opus55-round1/`.

The provenance records Claude Code in the Claude desktop app, with its harness reporting Opus 5.5 / `claude-opus-5-5`. That is a reported label, not independent verification of a backend snapshot. All ten prompts were read and answered in one repository-assistant conversation. Custom session instructions were present; backend snapshot, decoding seed and token billing are unknown. Preserve these limits and use the same collection procedure for the GPT arm.

## Next comparison

Collect the GPT arm in a fresh GPT-6.1 session using [the same teacher instruction](../../prompts/run-teacher-comparison.md), changing `ARM` to `gpt61`. Keep first outputs and failures, then perform the same audit and import. Compare meaning review, Qwen-token lengths and unchanged-student feedback before any downstream teacher-specific training. No student-feedback scoring or teacher-specific training has run for either arm yet.

These raw artifacts are ignored by Git and have not been uploaded. A teammate needs the private artifact archive to inspect exact teacher responses; the tracked prompt generator can reproduce the inputs, but a new chat response is a new stochastic sample.
