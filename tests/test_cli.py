import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research import ROOT


class CommandTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, "-m", "research", *arguments], cwd=ROOT,
                              capture_output=True, text=True, encoding="utf-8")

    def test_help_lists_the_complete_pipeline_without_loading_models(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ("doctor", "prepare", "rewrite", "score", "select", "train", "evaluate", "compare", "freeze"):
            self.assertIn(command, result.stdout)

    def test_final_test_requires_explicit_opt_in_before_reading_data(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("evaluate", "--split", "official-test", "--output", str(Path(directory) / "eval"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--final-test", result.stderr)

    def test_final_test_requires_frozen_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("evaluate", "--split", "official-test", "--final-test", "--output", str(Path(directory) / "eval"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--frozen-settings", result.stderr)

    def test_existing_output_is_preserved_before_any_download(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("prepare", "--output", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_zero_limit_is_rejected_instead_of_becoming_full_evaluation(self):
        result = self.run_cli("evaluate", "--limit", "0", "--output", "unused")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("positive", result.stderr)

    def test_final_test_requires_the_full_set(self):
        result = self.run_cli("evaluate", "--split", "official-test", "--final-test", "--frozen-settings", "unused.json",
                              "--limit", "1", "--output", "unused")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("full", result.stderr)

    def test_unplanned_evaluation_budget_is_rejected_before_loading_data(self):
        result = self.run_cli("evaluate", "--data", "does-not-exist", "--budget", "17", "--output", "unused")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("configured reasoning budgets", result.stderr)

    def make_evaluation(self, directory, training_ids, complete=True):
        directory.mkdir()
        manifest = {"config": {}, "data_manifest": {}, "split": "development", "budgets": [128], "subset": False,
                    "question_ids": ["a"], "adapter_run": {"training_ids": training_ids, "config": {"training": {}, "seed": 42},
                                                          "smoke_check": False, "unreviewed_screening": False}}
        (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (directory / "predictions.jsonl").write_text(json.dumps({"id": "a", "budget": 128, "correct": True, "output_tokens": 10}) + "\n", encoding="utf-8")
        if complete:
            (directory / "summary.json").write_text(json.dumps({"results": [{"budget": 128, "sample_size": 1}]}), encoding="utf-8")

    def test_comparison_rejects_different_training_question_sets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            self.make_evaluation(path / "left", ["train-0", "train-1"])
            self.make_evaluation(path / "right", ["train-0"])
            result = self.run_cli("compare", "--reference", str(path / "left"), "--candidate", str(path / "right"), "--output", str(path / "report.json"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("training", result.stderr)

    def test_comparison_rejects_interrupted_evaluations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            self.make_evaluation(path / "left", ["train-0"])
            self.make_evaluation(path / "right", ["train-0"], complete=False)
            result = self.run_cli("compare", "--reference", str(path / "left"), "--candidate", str(path / "right"), "--output", str(path / "report.json"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("complete", result.stderr)


if __name__ == "__main__":
    unittest.main()
