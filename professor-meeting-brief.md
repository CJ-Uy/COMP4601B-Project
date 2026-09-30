# Small language model research meeting

For professor feedback | Preferred meeting Tuesday 29 September 2026

**Decision requested:** Is the dialect study a sufficient course contribution, or would one of the alternatives be stronger?

## Compact reasoning dialects

**Say this:** “Can a small model solve problems using fewer tokens if we teach it a shorthand that mixes languages and symbols? We will test whether the language mixing actually helps beyond concise English, and whether choosing examples the model can use makes a difference.”

**Why it is not automatically novel:** Eight related papers are listed in sources 1–8. Multilingual reasoning, symbolic shorthand, compressed training examples, and student-aware selection already exist. Our candidate contribution is a controlled test of **whether multilingual access adds value beyond symbols and model feedback in a 0.6B model**. This is a provisional research gap, not a claim to have invented model languages.

### What we will do

1. **Start small.** Use Qwen3-0.6B and arithmetic word problems from GSM8K. Pilot on 100–200 training problems; target 1,500 for training, 300 for selection calibration, and 200 for development, all disjoint by original problem. Profile laptop time and memory first.
2. **Rewrite the same solutions.** Make four English-and-symbol versions and four English–Mandarin-and-symbol versions per problem. Preserve the same mathematical steps; check arithmetic and manually audit meaning. Keep the tokenizer fixed and count actual tokens.
3. **Choose useful examples.** Either take the shortest valid version, or show the frozen model a partial solution and test whether it can finish correctly. The partial solution must not reveal the answer. Initially try two completions per candidate, combine correctness with length, and check ranking stability on a subset.
4. **Train four small adapters.** Each starts from the same model, using the same problems and training recipe. Only the expression pool and selection rule change:

| Training examples | Shortest valid version | Model feedback plus length |
|---|---|---|
| English and symbols | Baseline A | Baseline B |
| English, Mandarin and symbols | Baseline C | Proposed method D |

5. **Test unaided.** Give each trained model only unseen questions. Compare D with B to test language mixing, and D with C to test selection. Also check the original model and concise English-only and Mandarin-only training. Use the untouched GSM8K test set plus 500 new arithmetic problems from held-out templates.
6. **Measure the trade-off.** Report answer accuracy, total output tokens, runtime, failures, and preparation/training cost. Freeze settings before testing; start with 256 scratchpad tokens plus 64 answer tokens. Aim for three training seeds and paired uncertainty estimates. Proposed target: 20% fewer tokens with at most a 3-percentage-point accuracy loss, supported by uncertainty bounds, against each primary comparator.

**Scope:** English–Mandarin first; Filipino next if feasible. Our English, Filipino, Waray-Waray, Mandarin and Cantonese knowledge supports manual review, but language coverage must be tested. No new vocabulary or training from scratch. Teacher choice and compute budget still need agreement.

**Still worthwhile if it fails:** A controlled finding that English and symbols work just as well would clarify when language mixing is unnecessary. Written scratchpads do not establish how the model thinks internally.

<!-- PAGEBREAK -->

# Backup ideas to pitch

Counts are selected examples, not field totals or novelty scores.

## 1 Selectively impair a language ability

**Pitch:** “Can we change a model internally so that it struggles with grammar while preserving meaning, rather than making it worse at everything?”

**Already done:** Three close lesion studies induce aphasia-like errors [9–11]; two come from the same research group. Targeted damage and adjustable severity are already explored.

**Possible difference:** Test whether Heretic-style directional edits preserve meaning better than component removal at matched grammar impairment. Compare intact, prompted and random-edit controls on unseen tasks. Using Heretic alone is not novelty; model errors are not human aphasia.

**Why / ask:** Tests which abilities can be separated. “Is intervention selectivity a sufficient contribution?”

## 2 A fly circuit decides when to stop reasoning

**Pitch:** “Can a tiny network built from mapped fly-brain connections learn when an LLM should stop working, using fewer training examples?”

**Already done:** Three adjacent papers cover adaptive stopping, connectome computing and fly-inspired adaptation [12–14]. Two public fly-language prototypes also exist [A–B]; FLM reports that its matched non-fly control did slightly better.

**Possible difference:** Compare actual wiring, a conventional recurrent controller and scrambled wiring, matching size, connection counts and inputs. Measure accuracy, tokens and total runtime as training data shrinks.

**Why / ask:** A testable efficiency question and memorable demo. “Is this worth the additional implementation work?”

## 3 Find which fly connections actually matter

**Pitch:** “If a fly-based controller helps, can we identify the wiring responsible and reproduce its benefit in a smaller artificial network?”

**Already done:** Connectome structure–function experiments are established [13]. This shares idea 2’s literature.

**Possible difference:** Compare targeted versus equally large random changes; reproduce any benefit in synthetic wiring. Damage causing worse performance alone is insufficient.

**Why / ask:** Explains why a controller works. “Would this strengthen idea 2?” Best treated as its follow-up.

## 4 A fly-inspired memory that handles corrections

**Pitch:** “Can a small memory module learn a correction without forgetting unrelated facts, while the language model stays frozen?”

**Already done:** Two adjacent papers already study fly-inspired continual learning [15–16]. Adding sparse memory alone is not new.

**Possible difference:** Test measured fly wiring against generic sparse memory and ordinary key-value/vector retrieval. Use invented facts, corrections and paraphrases; measure corrected-fact recall and interference at equal memory budgets.

**Why / ask:** Useful for noisy retrieval and selective updates. “Is this specific enough to justify a broader project?”

**Close the meeting:** “Which question is strongest? What comparison would convince you? Is a rigorous negative result enough for the course, and what should we cut to keep the study feasible?”

<!-- PAGEBREAK -->

# Selected research behind the pitches

Checked 27 September 2026. These are bounded novelty checks using primary abstracts, publication pages and project documentation, not a systematic review or independent reproduction. Exact-method novelty remains provisional. Titles below are shortened for scanning; links open the sources.

## Main idea

1. [EfficientXLang](https://arxiv.org/abs/2507.00246) (2025) — cross-language reasoning for token efficiency.
2. [The Impact of Language Mixing on Bilingual LLM Reasoning](https://aclanthology.org/2025.emnlp-main.1654/) (EMNLP 2025) — Chinese–English mixing and guided switching.
3. [Language-Mixed Chain-of-Thought](https://proceedings.iclr.cc/paper_files/paper/2026/hash/804b5e300c9ed4e3ea3b073f186f4adc-Abstract-Conference.html) (ICLR 2026) — training on mixed-language reasoning.
4. [ORION](https://arxiv.org/abs/2511.22891) (2025 preprint) — compact symbolic reasoning and brevity optimization.
5. [BabelTele](https://arxiv.org/abs/2606.19857) (2026 preprint) — compact nonstandard text for model consumption and communication.
6. [SCOReD](https://arxiv.org/abs/2607.05734) (2026 preprint) — student-aware reasoning edits for recommendation distillation.
7. [Multilingual CoT Compression via Cross-Lingual Distillation](https://aclanthology.org/2026.mellm-1.8/) (MeLLM 2026) — aligned multilingual data and concise reasoning training.
8. [Tailoring the Curriculum](https://arxiv.org/abs/2605.29229) (2026 preprint) — student-compatible data selection for reasoning distillation.

## Language impairment

9. [Bridging Brains and Models](https://arxiv.org/abs/2508.04749) (2025 preprint) — targeted expert lesions and retraining-based recovery.
10. [Component-Level Lesioning of Language Models](https://arxiv.org/abs/2601.19723) (2026 preprint) — targeted versus random damage and severity.
11. [Artificial Aphasias in Lesioned Language Models](https://arxiv.org/abs/2605.16222) (2026 preprint) — parameter lesions; model symptom distributions often differ from humans.

## Fly control and memory

12. [Think Faster Than Words](https://aclanthology.org/2026.acl-long.1330/) (ACL 2026) — adaptive shortcut decoding and early stopping.
13. [Connectome-based reservoir computing with conn2res](https://www.nature.com/articles/s41467-024-44900-4) (Nature Communications 2024) — fixed biological wiring with trained readouts.
14. [FlyLoRA](https://openreview.net/forum?id=nGQLYn13Xf) (NeurIPS 2025; [official code](https://github.com/gfyddha/FlyLoRA)) — fly-inspired sparse projections for model adaptation.
15. [Algorithmic insights on continual learning from fruit flies](https://arxiv.org/abs/2107.07617) (2021 preprint) — sparse coding and associative updates.
16. [FlyPrompt](https://arxiv.org/abs/2602.01976) (2026; [ICLR paper](https://openreview.net/pdf?id=8pi1rP71qv)) — fly-inspired routing and continual learning.

## Public implementations and study resources

A. [ngxson/fly-llm-hf](https://huggingface.co/ngxson/fly-llm-hf) — toy language model based on simulated fly wiring.
B. [FLM](https://github.com/nftechie/flm) — frozen language model coupled to a fly connectome; anatomy advantage not established.
C. [Heretic](https://github.com/p-e-w/heretic) — directional editing software; language-impairment objectives would require adaptation.

Planned main-study resources: [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B) and [GSM8K](https://huggingface.co/datasets/openai/gsm8k). Public implementations A–C are not included in paper counts.
