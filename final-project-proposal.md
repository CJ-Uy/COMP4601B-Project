# Compact multilingual reasoning for small language models

Project proposal | COMP 4901B Large Language Models | HKUST | 9 October 2026

Charles Joshua T. Uy | 21435832

Teammate name: ____________________ | Student ID: ____________________

## Problem and motivation

This project asks whether a small language model can solve arithmetic problems using shorter written reasoning. We will teach a shorthand that combines English, Mandarin and equations. For example, a sentence about three items costing five dollars each can become "3 x 5 = 15." Every shortened solution must preserve the calculations and answer.

We will start with [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), a small model suitable for our laptop experiment. A pilot will compare its feasibility with Qwen3-1.7B before fixing one model for all comparisons. We will measure tokens, the pieces of text a model processes, using that model's tokenizer. Fewer words alone do not establish lower computation costs.

Our contribution will be a controlled comparison of ordinary training, compact English reasoning and multilingual reasoning. We will also test whether feedback from the small model helps choose useful examples. Selecting examples only for brevity provides a simpler comparison. Together, these comparisons will show which changes improve efficiency while preserving accuracy.

## Related work

Earlier studies provide starting points for shorter reasoning. [EfficientXLang (Ahuja et al., 2025)](https://arxiv.org/abs/2507.00246) compares reasoning languages, while [ORION (Tanmay et al., 2025)](https://arxiv.org/abs/2511.22891) teaches compact symbolic solutions. [BabelTele (Zhu et al., 2026)](https://arxiv.org/abs/2606.19857) studies compressed communication between models. These studies motivate testing compact text that may be less natural for people to read.

Example selection and length control also have precedents. [SCOReD (Shahgir et al., 2026)](https://arxiv.org/abs/2607.05734) adapts reasoning examples to a student model in recommendation tasks. [AdaCtrl (Huang et al., 2025)](https://arxiv.org/abs/2505.18822) trains reasoning-length control. They inform our feedback procedure and an optional extension.

Our experiment will examine these ideas within one small model and one arithmetic task. Identical questions will be used across training conditions. Language choice and example selection will vary separately. This scope allows a manageable comparison of their effects.

## Data or tasks

[GSM8K](https://huggingface.co/datasets/openai/gsm8k) supplies 7,473 training problems and 1,319 test problems, with worked solutions. These are the dataset's official counts. Its numeric answers make correctness straightforward to check. The existing solutions will supply both our original-solution baseline and our rewrites.

We will randomly divide the training pool using a saved seed and problem IDs. We propose 1,000 training problems, including the 100-problem pilot, plus 300 separate calibration problems for choosing selection settings and 200 separate development problems for training settings. Calibration and development examples will not update model weights, and all versions of a question will stay together. These sizes are provisional, while the official test set remains untouched until settings are fixed.

Data checks will protect the comparison from faulty rewrites. Python will verify calculations, and both researchers will review a sample for changed meaning or missing steps. Invalid problem bundles will be removed from every condition. A separate transfer check will use 200 newly generated arithmetic problems with known answers and templates withheld during preparation.

## Method and baseline

The pilot will establish performance before fine-tuning. [Hugging Face Transformers](https://huggingface.co/docs/transformers/index), a Python library, will load the small model and generate its answers. Its tokenizer will count output tokens, while Python records correctness and elapsed time. These measurements will establish a reference for the trained versions.

A capable Claude or GPT model available to us will rewrite the supplied solutions, with [Ollama and Qwen3-8B](https://ollama.com/library/qwen3:8b) as a local fallback. We will fix the generator after the pilot and save its version, prompts and outputs. Each question receives four English-and-equation candidates and four allowing English, Mandarin and equations. Arithmetic checks and review must confirm preserved calculations, since a stronger generator does not guarantee useful compression.

Two selection rules will choose training examples. One selects the shortest valid candidate; the other gives the unchanged small model the first half of each candidate's solution steps and checks its final answer over two attempts. We will rank the latter candidates by correctness minus a token-length penalty, fixing the penalty weight on calibration data and rechecking a subset with eight attempts. This procedure tests whether brevity alone or the student's performance selects better examples.

We will train five conditions using [LoRA through Hugging Face PEFT](https://huggingface.co/docs/peft/main/package_reference/lora), which freezes the original model and learns small additions to its weights. The required baseline uses unchanged GSM8K English solutions; four rewritten conditions pair English or multilingual text with shortest-version or feedback-based selection. PyTorch and Transformers will handle training, with identical question IDs and settings, including a batch size chosen by the pilot. At evaluation, each model receives only the question, so these comparisons test learned solution formats rather than supplied answers.

## Evaluation

We will measure answer accuracy, generated tokens and elapsed time together. Python will compare final numeric answers with known answers and retain failed or unfinished outputs. Each condition will receive identical prompts and reasoning budgets of 128, 256 and 512 tokens, followed by up to 64 answer tokens. These controls will reveal whether compact training changes the accuracy gained from a given budget.

Our provisional target is 20 percent fewer output tokens with at most a three-percentage-point accuracy loss against relevant baselines. We will freeze evaluation settings before final testing and report uncertainty using the same questions across conditions. If resources permit, training will be repeated with three random seeds. Success must therefore reflect a matched comparison rather than a favourable choice of baseline.

Qualitative review will help explain the measurements. We will inspect 50 outputs for language switching, lost steps and calculation errors. Equal English performance or English-only outputs will limit the multilingual claim, and written steps cannot establish internal reasoning. Negative results will still identify where the proposed method fails.

## Resources and risks

The plan assumes two RTX 4060-class laptops, with available hosted models helping prepare examples. We will profile memory and time before expanding beyond the pilot. Five training conditions and candidate scoring must fit the remaining schedule. Actual costs will determine the final training size.

The main risks are incorrect rewrites and unreliable model feedback. Arithmetic checks and human review will address changed solutions, while repeated scoring will test selection stability. If feedback remains uninformative, we will narrow the task and report the change. Reinforcement learning through [verl](https://github.com/verl-project/verl) and GRPO is an optional extension that rewards correct, shorter answers after the core comparison is complete.

Reproducibility will be part of the deliverable. We will save prompts, model revisions, software versions, seeds, data IDs, code and costs, while excluding credentials. GSM8K uses an MIT license and Qwen uses Apache 2.0; attribution and hosted-model access terms will be recorded. Additional paid access or GPUs will require an agreed budget.

## Work plan

By the 29 October milestone, we will complete the 100-problem pipeline and train the original-solution baseline. We will test multilingual selection and profile training costs. A documented failure case will guide adjustments. The milestone will establish whether expansion is feasible.

After the milestone, we will expand training and complete all five conditions. One researcher will lead data preparation and language review, while the other leads selection, training and compute profiling. Both will inspect failures and check each other's work. Development settings will be fixed before final testing to preserve a fair evaluation.

We will present the findings on 24 to 26 November and submit the final report on 4 December. The report will explain the method, comparisons, costs and limitations. It will include negative results when the shorthand offers no advantage. The completed project will provide reproducible evidence for what compact multilingual training changes in a small model.
