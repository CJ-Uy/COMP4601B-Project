# Now You're Thinking My Language: Learning Compact Multilingual Reasoning Dialects for Sub-Billion Language Models

**Research proposal**  
**Course:** COMP 4901B, Large Language Models  
**Institution:** The Hong Kong University of Science and Technology  
**Team:** [Researcher 1] and [Researcher 2]  
**Date:** 20 September 2026

## Abstract

Multilingual speakers often combine languages when expressing an idea. This project asks whether small language models can learn a comparable form of compact reasoning: a scratchpad that combines short natural-language expressions, mathematical notation, and abbreviations according to what the model can use successfully. We will study a sub-billion language model and keep its tokenizer fixed. Our main comparison separates two factors: whether training examples allow multilingual expressions, and whether we select those examples using the model's ability to continue solving a problem correctly. This design will test whether multilingual choices provide an advantage beyond concise English, symbolic notation, and the selection procedure itself. We will begin with English and Mandarin, use arithmetic tasks with checkable answers, and train lightweight adapters on matched problem sets. Evaluation will measure answer accuracy, generated tokens, latency, and generalization to held-out problems. Existing research already covers compact symbolic reasoning, mixed-language distillation, and model-aware trace editing. Our proposed contribution is a controlled study of their intersection in sub-billion models, together with a reproducible procedure for selecting useful multilingual representations. We will report the conditions under which the method helps, fails, or offers no measurable advantage.

## 1. Motivation and research question

Our initial motivation comes from our multilingual background. The team can inspect English, Filipino, Waray-Waray, Mandarin, and Cantonese, which gives us a way to examine language mixing beyond automated translation scores. When people code-switch, a phrase in another language may feel shorter, clearer, or more natural. For a language model, however, fewer words or syllables do not necessarily mean fewer tokens. A compact phrase can also be difficult for a small model to interpret.

We therefore want to study the interaction between expression length and a model's ability to use that expression. The model will generate an intermediate scratchpad before answering a question. We use the term *reasoning dialect* for the recurring mixture of vocabulary, notation, and shorthand in that scratchpad. We will examine observable text and task performance. We will not infer the model's complete internal computation from its written scratchpad.

Our main research question is:

> Can multilingual reasoning dialects tailored to sub-billion language models improve their accuracy and token efficiency compared with equally trained English and symbolic reasoning?

In this proposal, *tailored to the model* has a specific meaning. We will select training representations partly by testing whether the target model can continue from them and reach a correct answer. The researchers will construct and validate the candidate pool; the model's measured performance will influence which candidates enter the training set.

The project has three supporting questions:

1. Does access to multilingual expressions improve the accuracy and token-cost trade-off once symbolic notation and training exposure are controlled?
2. Does selection based on model performance improve that trade-off relative to selecting the shortest valid expression?
3. Do the resulting patterns transfer to unseen problem structures and a larger reference model, or depend on the particular checkpoint and task?

We will treat improvements in accuracy and reductions in token use as separate outcomes. A method can be useful if it reduces tokens while preserving accuracy within a declared tolerance. We will only claim that it improves both if the measurements support both claims.

## 2. How prior work changed the direction

The project began with a broad question about using multiple languages inside a chain of thought. The literature required us to narrow that question several times. The table records those changes so that the proposed contribution is clear.

| Earlier version of the idea | Closest prior work | Consequence for this proposal |
|---|---|---|
| Use another language to reduce reasoning tokens. | [EfficientXLang](https://arxiv.org/abs/2507.00246) studies reasoning efficiency across languages and reports that non-English reasoning can reduce token use. | Comparing English with another language is a baseline, rather than our main contribution. |
| Mix languages within the reasoning process. | [The Impact of Language Mixing on Bilingual LLM Reasoning](https://aclanthology.org/2025.emnlp-main.1654/) examines code-switching, including phrase-level patterns. | The presence of code-switching cannot establish novelty. We must test what the switching contributes. |
| Teach the behavior through fine-tuning or distillation. | [Language-Mixed Chain-of-Thought](https://proceedings.iclr.cc/paper_files/paper/2026/hash/804b5e300c9ed4e3ea3b073f186f4adc-Abstract-Conference.html) trains models on mixed-language reasoning. [Think Multilingual, Not Harder](https://arxiv.org/abs/2604.15490) studies fine-tuning interventions that change code-switching behavior. | Moving from prompting to training is already established. Our training procedure needs a more specific purpose and comparison. |
| Train a small model to reason in compact shorthand. | [ORION](https://arxiv.org/abs/2511.22891) trains 1.5B models on compact symbolic reasoning and rewards concise correct solutions. | Small models, symbolic shorthand, and brevity rewards are already part of the literature. |
| Let the model learn a new compact reasoning vocabulary. | [Abstract Chain-of-Thought](https://arxiv.org/abs/2604.22709) learns a reserved vocabulary of abstract reasoning tokens. [Shorthand for Thought](https://arxiv.org/abs/2604.26355) learns larger tokens for recurring reasoning phrases. | We will keep the existing tokenizer and vocabulary fixed. Our experiment concerns the choice of expressions available in that vocabulary. |
| Combine multilingual fragments, abbreviations, and symbols. | [BabelTele](https://arxiv.org/abs/2606.19857) investigates this combination for compressed context and communication. [When LLMs Develop Languages](https://arxiv.org/abs/2606.29354) studies invented symbolic protocols for multi-agent reasoning. | The mixture itself is insufficient as a novelty claim. We will study a single small model learning to generate and use it during problem solving. |
| Adapt reasoning examples to what a small model understands. | [SCOReD](https://arxiv.org/abs/2607.05734) selects edits to teacher reasoning using student-model signals in recommendation tasks. | Model-aware selection is also established. We will examine whether it changes the value of multilingual expressions relative to matched English alternatives. |

Additional work constrains the scope. [Multilingual Chain-of-Thought Compression via Cross-Lingual Distillation](https://aclanthology.org/2026.mellm-1.8/) combines multilingual data construction with training for concise reasoning. [UL-XCoT](https://arxiv.org/abs/2604.20090) selects auxiliary languages and prunes reasoning trajectories to reduce inference cost. These studies make broad claims about multilingual compression or dynamic language selection unsuitable as our sole contribution.

We also considered approaches with different objectives. [AdaMame](https://arxiv.org/abs/2606.15080) and [Progressive Code-Switching](https://arxiv.org/abs/2607.00485) train models toward reasoning in the query or target language. Our proposed objective concerns correctness and cost, without requiring the scratchpad to match the question's language. [Coconut](https://arxiv.org/abs/2412.06769) investigates continuous latent reasoning. Our initial experiments will stay within ordinary discrete text generation so that we can inspect the representations and use standard fine-tuning tools.

### 2.1 Proposed contribution and its limits

The candidate contribution is a controlled test of multilingual representation selection for sub-billion models. We will compare English and multilingual candidate pools under the same two selection rules, then train the same starting model on the selected traces. This will let us estimate whether multilingual expressions add value, whether model feedback adds value, and whether the two interact.

The literature reviewed for this proposal does not establish that this exact experimental combination is already settled. The gap remains provisional. Existing studies already establish compact reasoning, multilingual reasoning, and model-aware distillation as research directions. Before fixing the final submission claim, we will compare the full methods and released code of the closest papers, especially ORION, BabelTele, SCOReD, and multilingual compression work.

Using fewer than one billion parameters defines the setting. A contribution would require a useful method, a reproducible finding about that setting, or an explanation of a failure. Running an existing approach on a smaller checkpoint would support a narrower replication claim.

## 3. Hypotheses

We will evaluate the following hypotheses without assuming that all will hold:

**H1: Multilingual access.** Under the same selection rule and comparable training exposure, a multilingual candidate pool can improve the target model's accuracy and token-cost trade-off relative to an English pool that already includes symbolic notation.

**H2: Model-guided selection.** Selecting representations using the model's continuation performance can preserve more useful information than selecting by token length alone.

**H3: Interaction.** The benefit of model-guided selection may differ between English and multilingual pools. This interaction will indicate whether tailoring is especially useful when the representation can cross language boundaries.

**H4: Dependence on the model.** Representations selected for one checkpoint may transfer imperfectly to another. Any difference will be described as checkpoint-dependent evidence. Two checkpoints cannot establish a universal minimum model size or isolate parameter count from pretraining differences.

A plausible null outcome is that compact English and mathematical notation perform as well as the multilingual conditions. That result would limit the claim that code-switching provides an additional efficiency advantage in our setting.

## 4. Scope, models, and languages

### 4.1 Model selection

The primary model will be [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), an openly released model with an Apache 2.0 license. The official model card identifies it as a 0.6B-parameter causal language model. It provides a practical starting point for a sub-billion experiment with multilingual reasoning behavior.

If time and compute permit, we will repeat the core comparison with [Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B). This larger checkpoint will be a reference condition. It will not replace the sub-billion focus.

We considered several smaller alternatives:

| Model | Possible role | Reason it is outside the initial core experiment |
|---|---|---|
| [Pythia-14M](https://huggingface.co/EleutherAI/pythia-14m) | Very small language-model research baseline | Its English focus and lack of instruction tuning introduce different training requirements. |
| [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) | Extension at a much smaller size | The model is primarily English-focused, so a failure on multilingual traces would not isolate capacity. |
| [SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) | Additional small-model comparison | The same language-coverage concern applies. |
| [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | Alternative sub-billion checkpoint | Comparing different model generations changes more than parameter count. |
| [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) | Later extension | Its architectural differences would complicate the initial comparison. |

We will record exact model revisions, tokenizer revisions, numerical precision, and chat templates before running experiments. Quantization will be treated as a memory-saving choice, rather than a reduction in parameter count.

### 4.2 Languages and representation

The core experiment will use English and Mandarin, with Mandarin text written consistently in Simplified Chinese. Mathematical notation and a controlled set of abbreviations will be available in both the English and multilingual conditions.

Filipino will be an extension after the core pipeline works. Cantonese and Waray-Waray will remain outside the initial training matrix. Including all five languages at once would make it harder to separate language coverage from the effect of the representation.

The multilingual condition will permit switching within a sentence or reasoning step. We will not require every trace to switch languages. Choosing English throughout can be a valid outcome if that representation is the most useful for the model.

## 5. Data and task design

### 5.1 Primary benchmark

We will use the official training and test partitions of [GSM8K](https://huggingface.co/datasets/openai/gsm8k). Arithmetic word problems provide numeric answers that can be checked without relying on an LLM judge.

The planned main training set contains 1,500 problems sampled from the official training partition. We will reserve 300 different training-partition problems for calibrating the selection procedure and 200 for model development. A pilot will use 100 to 200 training problems. These are planning targets and may be reduced after profiling, before final test evaluation.

We will split by original problem identity before producing translations, paraphrases, or alternative traces. All versions of a problem will remain in the same partition. If we remove a problem because a valid representation cannot be constructed for every core condition, we will remove it from every condition and report the exclusion rate and problem characteristics.

The official test set will remain untouched during prompt design, candidate selection, hyperparameter tuning, and checkpoint selection. We will save the split identifiers and dataset revision with the experiment configuration.

### 5.2 Generalization checks

We will create a separate set of 500 programmatically generated arithmetic problems with known derivations and answers. The generator will vary quantities, operation order, irrelevant facts, and wording. We will define and freeze its held-out templates before evaluating the trained models. These examples will provide a test of transfer beyond the public benchmark and reduce dependence on potentially memorized questions.

If compute permits, we will evaluate English and Mandarin inputs from [MGSM](https://huggingface.co/datasets/juletxara/mgsm), introduced in [Language Models are Multilingual Chain-of-Thought Reasoners](https://arxiv.org/abs/2210.03057). MGSM contains translations of the same underlying problems across languages. We will report paired language results and identify overlap with GSM8K. We will not count translated versions as independent evidence of generalization to new problem identities.

### 5.3 Trace construction and validation

For each training problem, we will construct a canonical sequence of solution steps from the reference solution. A fixed teacher model may assist with rewriting and translation, subject to access and budget. We will record its identifier, revision where available, prompts, sampling settings, and generation cost.

Every candidate will preserve the canonical operations, quantities, intermediate results, and final answer. Candidate differences will concern how the steps are expressed. Arithmetic checks will verify executable operations where possible. The team will inspect a stratified sample of translations and rewrites for omitted conditions, changed meanings, and premature disclosure of the final answer.

Correct final answers alone will not establish that all intermediate steps are valid. We will retain validation failures and their reasons in the data log.

## 6. Proposed method

### 6.1 Matched candidate pools

We will create two pools of four valid candidate traces per training problem:

**English pool.** Four concise English variants, including prose and symbolic shorthand.

**Multilingual pool.** Four variants with the same underlying solution and matched formatting choices. This pool will include an English fallback and variants that may combine English, Mandarin, and symbols. The corresponding English variants will express the same mathematical operations.

Both pools will offer the same number of candidates. We will inspect their length distributions and semantic coverage. A multilingual pool containing much more aggressive omissions would invalidate the intended comparison, even if its answers remain correct.

The tokenizer and vocabulary will remain fixed throughout. We will count tokens using the target model's tokenizer. We will not assume that a Chinese character, an abbreviation, or a mathematical symbol occupies a single token.

### 6.2 Two selection rules

We will apply both rules to both candidate pools.

**Length selection.** Choose the shortest candidate that passes semantic and arithmetic checks. Break ties using a fixed rule.

**Model-guided selection.** Choose a candidate using both its length and the target model's ability to continue solving from it.

For the second rule, we will select a shared intermediate step in each canonical solution. We will show the model the question and each candidate's prefix up to that step, then ask it to finish the problem. The prefix must stop before the final answer and before a step that states the requested result. The corresponding prefixes will contain the same mathematical information across languages and formats.

We will initially sample two continuations per candidate under a fixed generation budget. For candidate i, let p_i be the fraction of these continuations with a correct answer and let l_i be the full candidate's token length. A simple selection score is:

`score_i = p_i - lambda * (l_i / l_reference)`

Here, l_reference is the canonical trace length measured with the same tokenizer. We will choose lambda on the calibration split and then freeze it. The score is a practical selection rule assembled from established ideas. We do not claim the score itself as a new optimization principle.

Two continuations give a noisy estimate. We will repeat scoring with more samples on a small audit subset and report how often the selected candidate changes. We will also compare a shared middle-step cutoff with an earlier cutoff on that subset. If rankings are unstable, we will increase sampling for fewer training problems rather than present unstable scores as precise measurements.

All continuation scoring will use training or calibration problems. Final test questions and their answers will not enter the procedure. We will score candidates using a frozen copy of the starting model, then train adapters from that same starting checkpoint. Continuation performance is a proxy for the usefulness of a representation: it does not guarantee that the trained model can produce that representation unaided. Final evaluation will test that separate requirement.

### 6.3 Learning the dialect

We will fine-tune the model to generate the selected complete trace and answer from the question alone. This is supervised sequence distillation. During evaluation, the model will generate its own scratchpad without a teacher, a candidate search, or a language router running alongside it.

We will begin with [LoRA](https://arxiv.org/abs/2106.09685). If memory requires it, we will use a consistent [QLoRA](https://arxiv.org/abs/2305.14314) configuration across conditions. The initial configuration will use a small adapter rank, a microbatch of one, gradient accumulation, and a sequence limit chosen from training-length measurements. We will record any exclusions caused by the limit and avoid silently truncating solution targets.

For the core comparison, all conditions will use the same original problems, number of selected examples, training epochs, adapter configuration, optimizer, and update schedule. Their target token counts will differ because compression is part of the treatment. We will report those counts and the actual training cost. A smaller sensitivity experiment will equalize training-token exposure between the two strongest relevant conditions, so an apparent benefit cannot be attributed only to unequal token exposure.

We will freeze the training recipe using development data before running the final comparison. A successful pilot will establish basic format compliance and measurable reasoning performance before we expand the dataset.

## 7. Experimental conditions and controls

The core experiment is a two-by-two design:

| Condition | Available expressions | Selection rule | Purpose |
|---|---|---|---|
| E-L | English and symbols | Shortest valid trace | Compact monolingual baseline |
| E-F | English and symbols | Model-guided selection | Isolates feedback without multilingual access |
| M-L | English, Mandarin, and symbols | Shortest valid trace | Isolates multilingual access without model feedback |
| M-F | English, Mandarin, and symbols | Model-guided selection | Proposed combined condition |

The primary comparisons will be M-F against E-F, which tests multilingual access under the same selection rule, and M-F against M-L, which tests feedback within the multilingual pool. We will also report the interaction between pool type and selection rule. All four conditions are required for the main claim.

We will include three reference conditions:

- The unmodified starting checkpoint, evaluated with the same task instruction and budget protocol.
- An adapter trained on concise English prose, using the same problems and training recipe.
- An adapter trained on concise Mandarin reasoning, to test whether the apparent benefit comes from using Mandarin throughout.

The English symbolic conditions will serve as inexpensive conceptual controls for compact reasoning. We will label them as our controls, rather than as reproductions of ORION, whose full training procedure differs. Published results from other papers will provide context but will not substitute for matched experiments.

The four core conditions will use three training seeds if profiling supports the cost. Reference conditions will begin with one seed. If a reference becomes the strongest comparator or central to the conclusion, we will repeat it across seeds before making a comparative claim. If only one seed is affordable, the report will identify the result as preliminary and retain the full core design.

The optional transfer experiment for H4 will train Qwen3-1.7B on multilingual traces selected by Qwen3-0.6B and compare it with Qwen3-1.7B trained on traces selected using its own continuation scores. Both conditions will draw from the same candidate pool and problems, with the same training recipe. This comparison will test the value of selecting representations for the target checkpoint. If compute does not permit it, H4 will remain unanswered.

## 8. Evaluation and analysis

### 8.1 Accuracy and inference cost

We will evaluate one sampled answer per problem per run. We will not select the best answer from multiple attempts at test time. The same decoding settings will apply across conditions. We will begin with the Qwen3 model card's thinking-mode sampling guidance and freeze any task-specific adjustments on development data.

The primary budget will allow 256 scratchpad tokens, followed by a short final-answer allowance of up to 64 tokens. Secondary budgets of 128 and 512 scratchpad tokens will describe the trade-off. At the scratchpad cap, we will close the reasoning segment using the same protocol for all models and allow the final answer. We will report how often this intervention is required. An additional longer-budget check on a fixed subset will show whether conclusions depend on severe truncation.

The primary-budget experiment will use the complete official test partition. If the full budget sweep is too expensive, secondary budgets will use a fixed, randomly selected test subset chosen before inspecting any model's test answers. We will report the smaller sample size alongside those estimates.

We will measure:

| Measure | Definition |
|---|---|
| Answer accuracy | Fraction of problems with a correct normalized numeric answer |
| Scratchpad tokens | Tokens generated before the final-answer segment |
| Total generated tokens | All generated tokens, including delimiters, final answers, and failed outputs |
| Input tokens | Task instructions and problem text under the frozen tokenizer |
| Latency | End-to-end generation time under the same hardware and serving configuration |
| Failure rate | Missing answers, malformed output, repetition, and budget exhaustion |
| Preparation and training cost | Teacher tokens, continuation-scoring tokens, GPU time, and peak memory |

Numeric scoring will use a documented parser for fractions, decimals, signs, and units. It will extract one unambiguous answer from the final-answer segment. Ambiguous or unparseable outputs will count as failures, with a separate audit of parser errors. Reasoning that spills into the final-answer segment will still count toward total generated tokens. We will publish the scoring rules and representative cases.

Latency measurements will use warm-up runs, a fixed batch size, a consistent power mode, and interleaved condition order where practical. Laptop temperature and throttling can affect timing, so token counts and latency will be reported separately. Offline data generation and selection costs will also be reported separately from deployment inference cost.

### 8.2 Decision criteria and uncertainty

As a provisional engineering target, we seek at least 20% fewer total generated tokens with an accuracy loss no greater than 3 percentage points. We will apply this criterion separately to M-F versus E-F for the multilingual contribution and M-F versus M-L for the selection contribution. These are proposed decision thresholds, not expected results. We will review them using pilot and calibration data, document the final choices, and freeze them before final testing.

We will report paired confidence intervals for accuracy differences and token-cost ratios. We will resample by original problem identity, keeping related language versions together. Seed-level results will be shown separately as well as summarized. Repeated outputs of the same problem will not be treated as independent problems.

An accuracy-preservation claim will require the confidence interval to support the declared non-inferiority margin. A nonsignificant difference alone will not establish equivalence. We will report both primary comparisons even if only one favors the proposed method, and label additional subgroup analyses as exploratory.

### 8.3 What the learned traces contain

We will examine whether the trained model switches languages within steps, relies mostly on mathematical notation, or remains predominantly monolingual. If the multilingual condition converges on English-only traces, we will report that outcome without describing the output as a learned multilingual dialect.

The team will independently annotate an overlapping sample of 100 traces for language mixing, semantic errors, omitted steps, and unnecessary repetition. We will report agreement and resolve disagreements in a separate adjudication pass. Short fragments and shared Chinese writing can make language identification ambiguous, so we will separate natural-language spans from equations, names, and numerals.

A controlled prefix experiment will replace selected multilingual spans with meaning-matched English versions while preserving the problem and available mathematical information. It will test whether continuation performance changes. Since rewriting can alter length and phrasing, we will record those changes and avoid attributing every difference solely to language identity.

On synthetic tasks, we will also inspect operation-level correctness. Neither readable traces nor correct final answers will be presented as proof that the written trace fully describes the model's internal computation.

## 9. Compute and feasibility

The fallback resource plan assumes two RTX 4060-class gaming laptops. Actual VRAM, sustained throughput, and thermal limits remain to be measured. We will run independent jobs on the two machines; their GPU memory will not be treated as one pooled resource.

Before the main experiment, we will measure training time, generation throughput, and peak memory on a small batch. We will estimate the remaining workload from those measurements. For example, scoring 1,500 problems with up to eight candidates across both pools, two continuations per candidate, and a 256-token cap has a maximum continuation budget of about 6.1 million generated tokens. Shared candidates and early completion may reduce that count. Candidate construction and final evaluation add separate costs.

The core plan uses adapter training and one offline selection pass. Online reinforcement learning, new token embeddings, and training a language model from scratch are outside the initial scope. If necessary, we will reduce the number of training problems while retaining the four comparison conditions and the untouched test partition.

HKUST's [HPC4 service](https://itso.hkust.edu.hk/services/academic-teaching-support/high-performance-computing/hpc4) lists faculty members as principal investigators for account applications and uses a charging model. We will ask the course instructor or a supervisor whether this project can receive access under an eligible account. University GPU access is a possible extension, rather than an assumed resource.

A modest API or cloud budget may support teacher generation or larger reference runs. The team will set a spending ceiling after the pilot and before submitting paid batches. No particular provider, paid allocation, or university GPU has been secured by this proposal.

## 10. Schedule and division of work

The following ten-week schedule is a planning assumption. We will align it with the actual course deadlines once the submission requirements are confirmed.

| Week | Work | Deliverable |
|---|---|---|
| 1 | Read closest methods, fix scope, inspect model and dataset licenses, profile hardware | Literature comparison and experiment specification |
| 2 | Implement answer scoring, establish baseline performance, freeze data partitions | Reproducible baseline and split manifest |
| 3 | Construct pilot candidate pools and audit semantic equivalence | Validated pilot data and error log |
| 4 | Test continuation-based selection and train the four pilot conditions | Pilot report and decision on feasible scale |
| 5 to 6 | Expand the dataset and train the core conditions | Saved adapters, configurations, and cost logs |
| 7 | Complete seed repetitions and relevant reference conditions | Frozen checkpoints and evaluation protocol |
| 8 | Run final accuracy and cost evaluation | Results tables with uncertainty estimates |
| 9 | Analyze language behavior, failure cases, and generalization | Annotated traces and ablation results |
| 10 | Write the report, package reproducibility materials, prepare presentation | Final report, code, and presentation |

One researcher will lead data construction, language review, and evaluation. The other will lead model training, selection experiments, and compute profiling. Both will review the literature, independently annotate the shared trace sample, inspect failures, and write the final report. We will assign names once the team confirms this division.

## 11. Risks and responses

| Risk | Response |
|---|---|
| The starting model cannot solve enough examples to provide useful feedback. | Measure this in the pilot. Restrict the initial task difficulty or change the checkpoint before finalizing the protocol, and document the scope change. |
| Multilingual rewrites change the mathematical content. | Preserve canonical steps, use arithmetic checks, audit translations, and exclude invalid problem bundles from every condition. |
| Feedback scores are too noisy. | Repeat scoring on an audit subset, inspect ranking stability, and trade dataset size for more reliable measurements if needed. |
| The apparent gain comes from symbols or shorter prose. | Retain the English symbolic conditions, concise prose baseline, and paired content controls. |
| The model benefits from extra selection compute rather than multilingual access. | Compare both pools under the same feedback procedure and report all offline compute. |
| Code-switching reduces readability without improving efficiency. | Report the accuracy-cost result and annotation findings. Do not treat unusual-looking text as evidence of better reasoning. |
| The workload exceeds laptop capacity. | Reduce training examples or secondary evaluations, retain the core factorial comparison, and seek supervised university access if available. |
| New literature covers the same method before submission. | Update the related-work comparison and frame the contribution as replication, extension, or analysis as the evidence warrants. |
| The test benchmark was present in pretraining data. | Disclose this limitation and use newly generated held-out problems as an additional check. |

## 12. Expected contributions, reproducibility, and research practice

The intended outputs are:

1. A reproducible pipeline for constructing and selecting compact English and multilingual reasoning traces using a target model's continuation performance.
2. A controlled comparison that separates multilingual access from model-guided selection in a sub-billion language model.
3. An analysis of when compressed representations help or hurt, including token cost, language behavior, omitted information, and transfer to unseen problems.
4. A documented set of prompts, split identifiers, adapter configurations, evaluation rules, and representative successes and failures.

We will publish code and derived data where the source licenses and teacher-provider terms permit redistribution. If a source cannot be redistributed, we will provide identifiers and reconstruction instructions instead. We will retain all evaluated conditions, including unsuccessful ones, and distinguish pilot decisions from choices made after observing final results.

The study will use public or generated arithmetic data and will not require private student messages or personal writing samples. Team annotation will focus on linguistic and mathematical properties. If we later recruit external participants, we will follow the applicable course and university requirements for consent and data handling.

Potentially unreadable scratchpads may be harder to inspect. We will keep sampled original and rewritten traces, report semantic failures, and avoid presenting the learned representation as a faithful explanation of every internal computation. A useful course outcome can include a carefully measured negative result. Any later workshop submission will depend on the strength of the evidence and the final comparison with prior work.

## 13. Linked references

The references below include the studies that shaped this proposal, relevant adjacent work discussed during topic selection, and the methods and resources used in the experiment. Citations in the main text link directly to their sources. Recent preprints are evidence of prior proposals and reported experiments; their results have not been independently reproduced for this project.

### Reasoning, multilingualism, and compression

1. Ahuja, S., Vaddamanu, P., and Patra, B. (2025). [EfficientXLang: Towards Improving Token Efficiency Through Cross-Lingual Reasoning](https://arxiv.org/abs/2507.00246).
2. Li, Y., Xin, J., Miao, M. M., Long, Q., and Ungar, L. (2025). [The Impact of Language Mixing on Bilingual LLM Reasoning](https://aclanthology.org/2025.emnlp-main.1654/). EMNLP.
3. Son, G., et al. (2026). [Pushing on Multilingual Reasoning Models with Language-Mixed Chain-of-Thought](https://proceedings.iclr.cc/paper_files/paper/2026/hash/804b5e300c9ed4e3ea3b073f186f4adc-Abstract-Conference.html). ICLR.
4. Lin, E. M., and Jurgens, D. (2026). [Think Multilingual, Not Harder: A Data-Efficient Framework for Teaching Reasoning Models to Code-Switch](https://arxiv.org/abs/2604.15490).
5. Tanmay, K., Aggarwal, K., Liang, P. P., and Mukherjee, S. (2025). [ORION: Teaching Language Models to Reason Efficiently in the Language of Thought](https://arxiv.org/abs/2511.22891).
6. Ramji, K., Naseem, T., and Astudillo, R. F. (2026). [Thinking Without Words: Efficient Latent Reasoning with Abstract Chain-of-Thought](https://arxiv.org/abs/2604.22709).
7. Zhao, Z., Land, S., Bikel, D. M., and Alshikh, W. (2026). [Shorthand for Thought: Compressing LLM Reasoning via Entropy-Guided Supertokens](https://arxiv.org/abs/2604.26355). Use the revised version dated 14 September 2026 for the accuracy analysis.
8. Zhu, J., et al. (2026). [Large Language Models Do Not Always Need Readable Language](https://arxiv.org/abs/2606.19857). Introduces the BabelTele representation study.
9. Pei, Z., et al. (2026). [When LLMs Develop Languages: Symbolic Communication for Efficient Multi-Agent Reasoning](https://arxiv.org/abs/2606.29354).
10. Shahgir, H. S., et al. (2026). [SCOReD: Student-Aware CoT Optimization for Recommendation Distillation](https://arxiv.org/abs/2607.05734).
11. Wan, J., Zhang, S., and Chen, Y. (2026). [Multilingual Chain-of-Thought Compression via Cross-Lingual Distillation](https://aclanthology.org/2026.mellm-1.8/). MeLLM workshop.
12. Zhang, C., et al. (2026). [Less Languages, Less Tokens: An Efficient Unified Logic Cross-lingual Chain-of-Thought Reasoning Framework](https://arxiv.org/abs/2604.20090). UL-XCoT.
13. Ki, D., Duh, K., and Carpuat, M. (2026). [AdaMame: A Training Recipe for Adaptive Multilingual Reasoning](https://arxiv.org/abs/2606.15080).
14. Wang, Z., et al. (2026). [Efficient Multilingual Reasoning Transfer via Progressive Code-Switching](https://arxiv.org/abs/2607.00485).
15. Hao, S., et al. (2024). [Training Large Language Models to Reason in a Continuous Latent Space](https://arxiv.org/abs/2412.06769). Coconut.
16. Wei, J., et al. (2022). [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903). Background on explicit reasoning traces.

### Training methods and datasets

17. Hu, E. J., et al. (2021). [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685).
18. Dettmers, T., et al. (2023). [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314).
19. OpenAI. [GSM8K dataset and dataset card](https://huggingface.co/datasets/openai/gsm8k).
20. Shi, F., et al. (2022). [Language Models are Multilingual Chain-of-Thought Reasoners](https://arxiv.org/abs/2210.03057). [MGSM dataset and dataset card](https://huggingface.co/datasets/juletxara/mgsm).

### Model and compute resources

21. Qwen. [Qwen3-0.6B model card](https://huggingface.co/Qwen/Qwen3-0.6B) and [Qwen3-1.7B model card](https://huggingface.co/Qwen/Qwen3-1.7B).
22. Qwen. [Qwen2.5-0.5B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) and [Qwen3.5-0.8B model card](https://huggingface.co/Qwen/Qwen3.5-0.8B).
23. Hugging Face. [SmolLM2-135M-Instruct model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) and [SmolLM2-360M-Instruct model card](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct).
24. EleutherAI. [Pythia-14M model card](https://huggingface.co/EleutherAI/pythia-14m).
25. HKUST Information Technology Services Office. [HKUST HPC4 service, eligibility, and charging information](https://itso.hkust.edu.hk/services/academic-teaching-support/high-performance-computing/hpc4).

## Appendix: Details to confirm before submission

- Add the two researchers' names and any required student identifiers.
- Confirm the course's proposal length, required sections, deadline, and citation style. The supplied [Overleaf course link](https://www.overleaf.com/read/mwwgfqtzvctw#29c119) opened a join-project screen during preparation, so its contents could not be verified.
- Confirm the laptops' VRAM and available working time, then replace planning targets with measured workload estimates.
- Select the teacher model and confirm the permitted budget and data-redistribution terms before generating paid batches.
- Obtain instructor feedback on the provisional research gap and confirm whether university compute is available.
