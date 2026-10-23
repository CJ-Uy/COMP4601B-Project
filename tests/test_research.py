import copy
import tempfile
import unittest
from pathlib import Path

from research import core


def problem(index=0):
    return {"id": f"train-{index}", "question": "Three items cost five dollars each. Two dollars are added. Total?",
            "solution": "Items cost <<3*5=15>>15. Total <<15+2=17>>17.\n#### 17", "answer": "17"}


def candidate(pool="english", index=0):
    return {"id": "train-0", "pool": pool, "candidate": index,
            "steps": [{"text": "Items", "equation": "3 * 5 = 15"},
                      {"text": "Total", "equation": "15 + 2 = 17"}],
            "answer": "17", "reviewed": True, "tokens": 20, "feedback_accuracy": 0.5}


class AnswerTests(unittest.TestCase):
    def test_extracts_explicit_final_answer_not_an_intermediate_number(self):
        self.assertEqual(core.extract_answer("5 then 10.\n#### $1,234.50"), "2469/2")
        self.assertEqual(core.extract_answer("#### -3/2"), "-3/2")
        self.assertIsNone(core.extract_answer("I reached 17 but am still working"))
        self.assertIsNone(core.extract_answer("#### 1,2"))
        self.assertIsNone(core.extract_answer("#### 1/0"))
        self.assertIsNone(core.extract_answer("#### 17 or 18"))

    def test_safe_arithmetic_checks_exact_fractions_and_rejects_code(self):
        self.assertEqual(core.arithmetic("(1 / 3) * 3"), 1)
        for expression in ["__import__('os').getcwd()", "2**999999", "1/0", "True", "1e999"]:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                core.arithmetic(expression)

    def test_decimal_arithmetic_does_not_round_before_validation(self):
        self.assertNotEqual(core.arithmetic("0.10000000000000001"), core.arithmetic("0.1"))
        with self.assertRaises(ValueError):
            core.equation_signature("0.10000000000000001=0.1")


class DataTests(unittest.TestCase):
    def test_splits_are_repeatable_disjoint_and_keep_source_ids(self):
        rows = [problem(i) for i in range(10)]
        splits = core.make_splits(rows, {"train": 4, "calibration": 2, "development": 3}, 42)
        self.assertEqual(splits, core.make_splits(rows, {"train": 4, "calibration": 2, "development": 3}, 42))
        ids = [r["id"] for group in splits.values() for r in group]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([len(splits[name]) for name in ("train", "calibration", "development")], [4, 2, 3])
        with self.assertRaises(ValueError):
            core.make_splits(rows, {"train": 20}, 42)
        with self.assertRaises(ValueError):
            core.make_splits([problem(), problem()], {"train": 1}, 42)

    def test_jsonl_does_not_replace_existing_work(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl"
            core.write_jsonl(path, [problem()])
            with self.assertRaises(FileExistsError):
                core.write_jsonl(path, [])
            self.assertEqual(core.read_jsonl(path)[0]["id"], "train-0")

    def test_jsonl_uses_platform_independent_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl"
            core.write_jsonl(path, [{"id": "a"}])
            self.assertEqual(path.read_bytes(), b'{"id": "a"}\n')

    def test_data_identity_ignores_machine_metadata_but_keeps_question_ids(self):
        first = {"model": "student", "model_revision": "abc", "dataset": "gsm8k", "dataset_revision": "def",
                 "dataset_config": "main", "seed": 42, "sizes": {"train": 1}, "ids": {"train": ["a"]},
                 "environment": {"gpu": "one"}, "config": {"epochs": 1}, "files": {"train.jsonl": "hash"}}
        second = dict(first, environment={"gpu": "two"}, config={"epochs": 3})
        self.assertEqual(core.data_identity(first), core.data_identity(second))
        second["ids"] = {"train": ["b"]}
        self.assertNotEqual(core.data_identity(first), core.data_identity(second))

    def test_candidate_checks_answer_equations_and_preserved_steps(self):
        self.assertEqual(core.validate_candidate(candidate(), problem()), [])
        for modify in [lambda c: c.update(answer="18"),
                       lambda c: c["steps"][0].update(equation="3*5=14"),
                       lambda c: c["steps"].pop(0),
                       lambda c: c["steps"][0].update(text="#### 17"),
                       lambda c: c["steps"][0].update(text="价格")]:
            bad = candidate()
            modify(bad)
            self.assertTrue(core.validate_candidate(bad, problem()))
        multilingual = candidate("multilingual")
        multilingual["steps"][0]["text"] = "价格"
        self.assertEqual(core.validate_candidate(multilingual, problem()), [])

    def test_feedback_prefix_excludes_final_answer(self):
        self.assertEqual(core.feedback_prefix(candidate()), "Items 3 * 5 = 15\n")
        bad = candidate()
        bad["steps"][0]["equation"] = "17=17"
        with self.assertRaises(ValueError):
            core.feedback_prefix(bad)

    def test_selects_five_conditions_on_identical_valid_ids(self):
        rows = [candidate(pool, i) for pool in ("english", "multilingual") for i in range(2)]
        for row in rows:
            if row["candidate"] == 1:
                row.update(tokens=30, feedback_accuracy=1.0)
        result, excluded = core.select_conditions([problem(), problem(1)], rows, 2, 0.1)
        self.assertEqual(set(result), {"original", "english-shortest", "english-feedback", "multilingual-shortest", "multilingual-feedback"})
        self.assertTrue(all([r["id"] for r in group] == ["train-0"] for group in result.values()))
        self.assertEqual(result["english-shortest"][0]["candidate"], 0)
        self.assertEqual(result["english-feedback"][0]["candidate"], 1)
        self.assertEqual(excluded[0]["id"], "train-1")

    def test_selection_rejects_unknown_duplicate_or_unscored_candidates(self):
        rows = [candidate(pool) for pool in ("english", "multilingual")]
        for bad in [rows + [copy.deepcopy(rows[0])], [dict(rows[0], id="unknown")],
                    [dict(rows[0], feedback_accuracy=None), rows[1]]]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                core.select_conditions([problem()], bad, 1, 0.1)

    def test_invalid_bundle_is_excluded_even_from_original_baseline(self):
        rows = [candidate("english"), candidate("multilingual")]
        rows[1]["steps"][0]["equation"] = "3*5=14"
        result, excluded = core.select_conditions([problem()], rows, 1, 0.1)
        self.assertTrue(all(not group for group in result.values()))
        self.assertEqual(excluded[0]["id"], "train-0")

    def test_unscorable_prefix_cannot_win_feedback_selection(self):
        rows = [candidate("english"), candidate("multilingual")]
        rows[1]["feedback_error"] = "Partial solution reveals the final answer"
        result, excluded = core.select_conditions([problem()], rows, 1, 0.1)
        self.assertTrue(all(not group for group in result.values()))

    def test_equivalent_numeric_answers_stay_canonical_in_training_rows(self):
        rows = [candidate("english"), candidate("multilingual")]
        rows[0]["answer"] = "17.0"
        result, _ = core.select_conditions([problem()], rows, 1, 0.1)
        self.assertEqual(result["english-shortest"][0]["answer"], "17")
        self.assertTrue(result["english-shortest"][0]["solution"].endswith("#### 17"))


class MetricsTests(unittest.TestCase):
    def test_failures_and_truncations_stay_in_accuracy_denominator(self):
        summary = core.summarize([
            {"correct": True, "output_tokens": 10, "seconds": 1, "error": None, "truncated": False},
            {"correct": False, "output_tokens": 20, "seconds": 3, "error": None, "truncated": True},
            {"correct": False, "output_tokens": 0, "seconds": 2, "error": "out of memory", "truncated": False}])
        self.assertEqual(summary["sample_size"], 3)
        self.assertEqual(summary["accuracy"], 1/3)
        self.assertEqual(summary["failures"], 1)
        self.assertEqual(summary["truncated"], 1)
        self.assertEqual(summary["mean_output_tokens"], 10)
        self.assertEqual(summary["mean_seconds"], 2)
        with self.assertRaises(ValueError):
            core.summarize([])

    def test_training_masks_prompt_and_keeps_end_token(self):
        feature = core.mask_training_tokens([1, 2], [1, 2, 3, 4, 5], 5)
        self.assertEqual(feature["labels"], [-100, -100, 3, 4, 5])
        self.assertEqual(feature["attention_mask"], [1, 1, 1, 1, 1])
        with self.assertRaises(ValueError):
            core.mask_training_tokens([1, 2], [1, 2, 3, 4, 5], 4)
        with self.assertRaises(ValueError):
            core.mask_training_tokens([1, 9], [1, 2, 3], 5)

    def test_unknown_failed_token_counts_are_not_reported_as_zero_cost(self):
        summary = core.summarize([
            {"correct": True, "output_tokens": 10, "seconds": 1, "error": None},
            {"correct": False, "output_tokens": None, "seconds": 2, "error": "out of memory"}])
        self.assertEqual(summary["accuracy"], 0.5)
        self.assertEqual(summary["mean_output_tokens"], 10)
        self.assertEqual(summary["token_measurements"], 1)
        left = [{"id": "a", "correct": True, "output_tokens": 20}]
        right = [{"id": "a", "correct": False, "output_tokens": None, "error": "out of memory"}]
        self.assertIsNone(core.paired_comparison(left, right, 42)["token_reduction"])

    def test_comparison_requires_same_questions_and_counts_paired_differences(self):
        left = [{"id": "a", "correct": True, "output_tokens": 20}, {"id": "b", "correct": False, "output_tokens": 20}]
        right = [{"id": "a", "correct": True, "output_tokens": 10}, {"id": "b", "correct": False, "output_tokens": 10}]
        result = core.paired_comparison(left, right, 42)
        self.assertEqual(result["accuracy_difference"], 0)
        self.assertEqual(result["token_reduction"], 0.5)
        self.assertEqual(result["accuracy_difference_95_ci"], [0, 0])
        with self.assertRaises(ValueError):
            core.paired_comparison(left, right[:1], 42)


if __name__ == "__main__":
    unittest.main()
