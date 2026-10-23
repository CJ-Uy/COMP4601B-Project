# Project instructions for contributors and coding assistants

This repository is the whole compact multilingual reasoning research project, including its Python experiments, written research documents and public explainer website. Keep enough context in tracked files for a teammate to work without access to the original chat or one developer's machine.

## Read first

1. `README.md`: setup, commands, artifact layout and reproduction.
2. `docs/TEAM_GUIDE.md`: research question, experimental design, status and open decisions.
3. `final-project-proposal.md`: current study proposal; older meeting briefs and `research-proposal.md` are historical drafts.
4. `docs/EXPERIMENT_LOG.md`: decisions and run handoffs.

The folder name contains COMP4601B, while the current proposal identifies the course as COMP 4901B Large Language Models. Preserve that distinction; do not silently rewrite course metadata or historical documents.

## Code and commands

- `research/` is the Python experiment package. Keep it independent of `explainer/`.
- `configs/pilot.json` is the proposed starting configuration. Follow the root README to create the local Python 3.12 environment.
- Python tests: `.venv/Scripts/python.exe -m unittest discover -s tests -v` on Windows, `.venv/bin/python -m unittest discover -s tests -v` on Linux.
- Website tests: `npm --prefix explainer run check` after installing its dependencies.
- Environment check: `.venv/Scripts/python.exe -m research doctor`.
- Use the smallest complete change. Reuse the standard library and installed dependencies. Test nontrivial parsing, selection and evaluation changes.
- Use Codebase Memory graph discovery when available, check coverage for relied-on files, and read source for stale/unindexed ranges. A teammate without the graph server can read source and search with `rg`; graph access is not required to run the project.

## Research rules

- Use saved original question IDs and disjoint train/calibration/development groups. Keep every rewrite with its source question.
- Preserve all five matched conditions, including training on unchanged GSM8K solutions. Never compare rewritten conditions against an original baseline with different retained IDs.
- Count tokens with the selected student's tokenizer. Word counts are not token measurements.
- Arithmetic validation is insufficient to establish unchanged meaning. Keep human review explicit.
- Candidate feedback uses the unchanged student and a partial solution without the final answer. Never use a trained adapter or development/test labels to choose training examples.
- Keep Qwen thinking mode, prompts, generation budgets and decoding settings consistent across conditions.
- Include failures and truncations in evaluation records. Do not drop inconvenient outputs, invent measurements or convert missing token measurements into zero-cost successes.
- Keep the official test set reserved until settings are fixed. Final evaluation needs the explicit CLI opt-in and frozen settings. Do not tune on final test results.
- Label smoke checks and unreviewed screening runs. Neither establishes a research result.
- Record model/dataset revisions, packages, config, seeds, question IDs, teacher provenance and costs. Document changed decisions rather than silently updating historical runs.

## Files, privacy and handoff

- `.venv/`, `.cache/`, `artifacts/`, `.env` files and credentials are local and ignored. Never put them in `explainer/public/`.
- Keep adapters, raw predictions, prompts and manifests together when sharing an experiment archive. Ignored artifacts need a separate backup; Git does not carry them to a teammate.
- Use new output directories. Preserve earlier results and user-provided documents.
- The public site deploys only `explainer/public/`. Do not publish research data, personal recordings, student IDs, credentials or screening results through site updates.
- External API spending, bulk teacher generation, full training runs and public deployment are explicit research actions, not routine tests. Setup should remain usable without hosted API credentials.
- Before handing off, update setup instructions, the context guide or experiment log when behavior or a research decision changes. State exactly what was verified and what remains untested.
