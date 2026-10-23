# GPT-6.1 versus Opus 5.5 as teachers

The user chose **two teachers generating training solutions**, with outputs exported from their ChatGPT and Claude accounts. The student remains Qwen3-0.6B. We compare the teaching material and, subsequently, students trained on it; we do not train the hosted teachers.

**Status on 24 October 2026:** shared prompts prepared; neither teacher's responses have been collected. The original-solution student baseline is trained and its quick development evaluation is running. No teacher quality result exists yet.

## First round: ten matched training questions

Use the first ten IDs in the saved pilot training partition. Both teachers receive exactly the same ten prompt files, including each original question and supplied solution. Each prompt requests four English/equation and four multilingual/equation candidates: 80 candidates per teacher, 160 in total. These batched prompts differ from the Ollama command's one-candidate-per-request protocol; do not pool those runs.

Create the pack from the repository root after preparing the locked pilot data:

```powershell
.venv\Scripts\python.exe -m scripts.prepare_teacher_comparison --output artifacts/teacher-comparison/chat-export-round1
```

The script uses no model or API, verifies split hashes and the committed data lock, and refuses to overwrite a directory. It saves the ten inputs, prompt files and their SHA-256 hashes in `manifest.json`. The tracked template is [teacher-comparison-v1.txt](../prompts/teacher-comparison-v1.txt). To repeat the round, choose a new output directory.

If opening this repository in a coding assistant with Opus or GPT selected, use the [copy-and-paste teacher instruction](../prompts/run-teacher-comparison.md). Change only `ARM` between teachers and use the same collection procedure for both. A shared repository conversation has different context from isolated chat prompts; record which procedure was actually used.

1. In ChatGPT, explicitly select GPT-6.1. In Claude, explicitly select Opus 5.5. Record the exact displayed model name and any mode/effort setting. If the requested model is unavailable, record that and stop that arm; do not silently substitute another model.
2. Use a fresh chat for every question, without project instructions, memory, attachments, web search or other tools where the interface lets you disable them. Record anything that cannot be controlled. Paste the full corresponding prompt file unchanged into each service.
3. Save the complete first response and conversation export under the teacher's `raw/` directory. Record prompt ID, timestamp/timezone, displayed model, mode, response/export location and any failure. Keep both successful and failed responses. Do not regenerate only the weaker teacher's answers or repair mathematics manually.
4. Save the eight returned JSON objects as UTF-8 JSONL, one object per line, in `gpt61/raw/<question-id>.jsonl` or `opus55/raw/<question-id>.jsonl`. Preserve the original response separately if stripping Markdown fences is necessary. Keep `reviewed: false` until a person checks meaning. An incomplete or malformed answer is a recorded failure, not grounds to choose a more convenient replacement question.
5. Once all ten responses are saved, combine the JSONL objects and import each teacher separately using the commands below. Check that each arm has 80 unique `(id, pool, candidate)` combinations, with indices 0–3 in both pools for every ID. Report missing/invalid combinations in the denominator of 80. Never fabricate missing candidates.

Combine one arm's ten response files (change `gpt61` to `opus55` for the other):

```powershell
.venv\Scripts\python.exe -c "from pathlib import Path; from research import core; p = Path('artifacts/teacher-comparison/chat-export-round1/gpt61'); core.write_jsonl(p / 'candidates.jsonl', [row for f in sorted((p / 'raw').glob('*.jsonl')) for row in core.read_jsonl(f)])"
```

Import into new directories. Replace the provenance labels below with the actual recorded UI selections, dates and modes, and retain the exports alongside the pack:

```powershell
.venv\Scripts\python.exe -m research rewrite --limit 10 --import-file artifacts/teacher-comparison/chat-export-round1/gpt61/candidates.jsonl --teacher-label "ChatGPT: actual model, mode, date; teacher-comparison-v1; chat-export-round1/gpt61/raw" --output artifacts/rewrites/teacher-gpt61-round1
.venv\Scripts\python.exe -m research rewrite --limit 10 --import-file artifacts/teacher-comparison/chat-export-round1/opus55/candidates.jsonl --teacher-label "Claude: actual model, mode, date; teacher-comparison-v1; chat-export-round1/opus55/raw" --output artifacts/rewrites/teacher-opus55-round1
```

The importer checks calculations and structure and saves validation errors. It does not prove semantic equivalence or enforce the expected 80-row completeness check. Both researchers should review the ten-question round against the source solutions, preferably with teacher identity hidden. Preserve the raw data and record reviewer decisions separately.

## What we compare

For each teacher and each language pool, record:

| Measure | What it tells us |
|---|---|
| Present, parseable and arithmetic-valid candidates / 40 | Format and calculation reliability, including failed/missing output |
| Human meaning-preserving candidates / 40 | Whether compact wording still explains the supplied solution |
| Student-token lengths of valid, reviewed solutions | Compression under Qwen's tokenizer; also show matched-question comparisons to avoid rewarding exclusions |
| Frozen student's partial-solution success | Whether the unchanged student can use the candidate; use the same attempts, seeds and prefix policy for both arms |
| Review time, retries, collection time and available usage/cost data | Practical effort; mark unavailable UI token billing as unknown |

Use the existing `score` command separately on each imported arm after the baseline GPU evaluation finishes. Do not run competing GPU workloads while measuring latency. Inspect per-question results as well as averages; ten questions support feasibility screening, not a reliable claim that one teacher is superior. Record which candidates were excluded and why. A shorter response alone does not establish a better teacher.

## Student training comparison

Keep GPT-6.1 and Opus 5.5 datasets and adapters separate. To test downstream benefit, generate both arms for the same 100 training questions, retain a common set of eligible IDs, and train the same four rewrite conditions for each teacher. Reuse or retrain the original-solution adapter on exactly that common ID set. This full design has nine trained conditions: one original and four rewrites for each teacher, plus the unchanged pretrained reference. Use identical training settings and held-out evaluation questions.

The ten-question round is preparation for that comparison; it is not a replacement for 100-question training. If resources require a smaller downstream comparison, agree on a common condition and common IDs for both teachers first and label the reduced design explicitly. Reserve the official test set until these choices are fixed.

## Provenance and account limits

For each teacher, save an adjacent `PROVENANCE.md` with the exact UI label, date/time, mode/effort, relevant settings, prompt-pack hash, all response/export filenames, failures/retries, review records, and usage/cost information if available. Subscription access does not supply an API experiment's token billing or a pinned backend snapshot; write `unknown` where the interface does not expose a value. Capture the actual account selections rather than claiming API model IDs were used.

The official API documentation currently names [`gpt-6.1-sol`](https://developers.openai.com/api/docs/models/gpt-6.1-sol) and [`claude-opus-5-5`](https://platform.claude.com/docs/en/models/opus-5-5/overview). Those are references for a future API replication; this round uses chat exports. All raw outputs and manifests stay in ignored `artifacts/` and need a separate private handoff archive. No credentials belong in the repository.
