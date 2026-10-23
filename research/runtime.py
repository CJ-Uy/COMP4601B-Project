"""Hugging Face model loading, generation and LoRA training."""

from datetime import datetime, timezone
import importlib.metadata
import json
import platform
import subprocess
import time

from . import ROOT, core


def environment():
    packages = {}
    for name in ("torch", "transformers", "datasets", "peft", "accelerate"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    result = {"python": platform.python_version(), "platform": platform.platform(),
              "packages": packages, "utc": datetime.now(timezone.utc).isoformat()}
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    result["git_commit"] = git.stdout.strip() if git.returncode == 0 else None
    git = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    result["git_dirty"] = bool(git.stdout.strip())
    if packages["torch"]:
        import torch
        result["cuda_available"] = torch.cuda.is_available()
        result["cuda_runtime"] = torch.version.cuda
        if result["cuda_available"]:
            result["gpu"] = torch.cuda.get_device_name(0)
            result["vram_bytes"] = torch.cuda.get_device_properties(0).total_memory
    return result


def question_prompt(question):
    return ("Solve the arithmetic problem. Write concise calculation steps, then end with "
            "a line containing #### followed by only the numeric answer.\n\n" + question)


class ModelRunner:
    def __init__(self, config, manifest, adapter=None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.bfloat16 if self.device == "cuda" and torch.cuda.is_bf16_supported() else torch.float32
        revision = manifest["model_revision"]
        self.tokenizer = AutoTokenizer.from_pretrained(config["model"], revision=revision, local_files_only=True)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        self.model = AutoModelForCausalLM.from_pretrained(config["model"], revision=revision,
                                                       dtype=self.dtype, attn_implementation="sdpa", local_files_only=True).to(self.device)
        if adapter:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, str(adapter))
        self.model.eval()

    def prompt_tokens(self, question):
        return self.tokenizer.apply_chat_template(
            [{"role": "user", "content": question_prompt(question)}],
            tokenize=True, add_generation_prompt=True, enable_thinking=False)

    def answer(self, question, budget, seed, prefix=""):
        import torch
        from transformers import set_seed

        set_seed(seed)
        tokenizer = self.tokenizer
        prompt = self.prompt_tokens(question) + tokenizer.encode(prefix, add_special_tokens=False)
        inputs = torch.tensor([prompt], device=self.device)
        sampling = {"do_sample": True, "temperature": self.config["temperature"],
                    "top_p": self.config["top_p"], "top_k": self.config["top_k"],
                    "pad_token_id": tokenizer.pad_token_id}
        if self.device == "cuda":
            torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            output = self.model.generate(input_ids=inputs, attention_mask=torch.ones_like(inputs),
                                         max_new_tokens=budget, stop_strings=["####"], tokenizer=tokenizer, **sampling)
            reasoning_ids = output[0, len(prompt):].tolist()
            reasoning = tokenizer.decode(reasoning_ids, skip_special_tokens=True)
            found_marker = "####" in reasoning
            eos = self.model.generation_config.eos_token_id
            eos = eos if isinstance(eos, list) else [eos]
            continuation = output[0].tolist()
            ended = bool(reasoning_ids and reasoning_ids[-1] in eos)
            if ended:
                continuation.pop()
            injected = tokenizer.encode(" " if found_marker else "\n#### ", add_special_tokens=False)
            continuation += injected
            final_input = torch.tensor([continuation], device=self.device)
            final = self.model.generate(input_ids=final_input, attention_mask=torch.ones_like(final_input),
                                        max_new_tokens=self.config["answer_budget"], **sampling)
            answer_ids = final[0, len(continuation):].tolist()
        if self.device == "cuda":
            torch.cuda.synchronize()
        answer_text = tokenizer.decode(answer_ids, skip_special_tokens=True).strip()
        predicted = core.extract_answer("#### " + answer_text)
        return {"output": reasoning + (" " if found_marker else "\n#### ") + answer_text,
                "predicted_answer": predicted, "reasoning_tokens": len(reasoning_ids),
                "answer_tokens": len(answer_ids), "output_tokens": len(reasoning_ids) + len(answer_ids),
                "prompt_tokens": len(prompt), "injected_answer_tokens": len(injected),
                "seconds": time.perf_counter() - started,
                "truncated": (len(reasoning_ids) == budget and not found_marker and not ended)
                             or (len(answer_ids) == self.config["answer_budget"] and answer_ids[-1] not in eos),
                "error": None, "seed": seed}


def training_features(runner, rows, max_length):
    features = []
    for row in rows:
        prompt = runner.prompt_tokens(row["question"])
        completion = runner.tokenizer.encode(row["solution"] + runner.tokenizer.eos_token, add_special_tokens=False)
        try:
            features.append(core.mask_training_tokens(prompt, prompt + completion, max_length))
        except ValueError as error:
            raise ValueError(f"{row['id']}: {error}") from error
    return features


def train_adapter(runner, rows, config, output, max_steps=-1):
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import DataCollatorForSeq2Seq, Trainer, TrainingArguments, set_seed

    settings = config["training"]
    set_seed(config["seed"])
    features = training_features(runner, rows, settings["max_length"])
    if not features:
        raise ValueError("No training questions remain")
    runner.model.config.use_cache = False
    model = get_peft_model(runner.model, LoraConfig(
        task_type="CAUSAL_LM", r=settings["lora_rank"], lora_alpha=settings["lora_alpha"],
        lora_dropout=settings["lora_dropout"], target_modules="all-linear", bias="none"))
    model.print_trainable_parameters()
    arguments = TrainingArguments(
        output_dir=str(output / "checkpoints"), num_train_epochs=settings["epochs"],
        max_steps=max_steps, learning_rate=settings["learning_rate"],
        per_device_train_batch_size=settings["batch_size"],
        gradient_accumulation_steps=settings["gradient_accumulation_steps"],
        bf16=runner.dtype == torch.bfloat16, fp16=False,
        gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="adamw_torch", save_strategy="no", logging_steps=1, report_to="none",
        dataloader_num_workers=0, dataloader_pin_memory=runner.device == "cuda",
        seed=config["seed"], data_seed=config["seed"], use_cpu=runner.device == "cpu")
    trainer = Trainer(model=model, args=arguments, train_dataset=Dataset.from_list(features),
                      processing_class=runner.tokenizer,
                      data_collator=DataCollatorForSeq2Seq(runner.tokenizer, label_pad_token_id=-100, pad_to_multiple_of=8))
    if runner.device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    result = trainer.train()
    model.save_pretrained(output / "adapter")
    runner.tokenizer.save_pretrained(output / "adapter")
    return {"metrics": result.metrics, "seconds": time.perf_counter() - started,
            "peak_vram_bytes": torch.cuda.max_memory_allocated() if runner.device == "cuda" else None,
            "training_examples": len(rows), "max_sequence_tokens": max(len(f["input_ids"]) for f in features),
            "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad)}
