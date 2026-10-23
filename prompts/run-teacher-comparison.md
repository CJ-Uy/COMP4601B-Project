# Copy into a fresh teacher session

Use the same instruction for both models. Set `ARM=opus55` when the selected model is Opus 5.5, and `ARM=gpt61` when it is GPT-6.1. This instruction is for a coding assistant with access to this repository. A new clone also needs the generated prompt pack; see `docs/TEACHER_COMPARISON.md`.

```text
You are a teacher generating compact training solutions for our Qwen3-0.6B study.
ARM=opus55
ROOT=artifacts/teacher-comparison/chat-export-round1

Your task is only to produce this teacher arm's candidate solutions. Do not change code, prompts, configuration or datasets, run training/evaluation, judge which teacher is better, or read the other teacher's outputs. Do not call another model or use web search to generate the solutions.

Read ROOT/manifest.json and the ten files it lists under ROOT/prompts/. If the pack is missing or the selected model is not the requested teacher, report that and stop; do not substitute questions or models.

For each prompt, follow its instructions exactly. Produce all eight candidates yourself: four English and four multilingual, numbered 0–3 within each pool. Keep reviewed=false. Preserve the supplied calculations, quantities, meaning and final answer. Do not add or remove steps to obtain a shorter solution.

Save your complete first response to each prompt as UTF-8 JSONL in ROOT/ARM/raw/<question-id>.jsonl, with one JSON object per line and no Markdown fences. Do not overwrite existing responses. Do not inspect scores or regenerate only failed candidates. If you cannot complete a question, preserve the failure in a separate text record and report the missing candidates rather than inventing them.

Create ROOT/ARM/PROVENANCE.md recording the actual selected model label, date/time, mode/effort and settings you can verify, which prompt files you used, and failures. Record that these outputs were produced in one repository-assistant conversation if that is how you ran them. Mark unavailable backend version, seed, usage or cost as unknown; do not infer them from the requested model name.

Do not mark anything human-reviewed. When finished, list the files created, total candidate count and missing/failed question IDs. Leave scoring and comparison to the common evaluation pipeline.
```

For stricter isolation, use a fresh conversation for each question and paste that question's prompt directly. If using the single instruction above, use the same shared-conversation procedure for both teachers and report that limitation. These alternatives are different collection protocols; do not silently mix them between arms.
