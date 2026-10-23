import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import ROOT, core
from research.__main__ import digest
from scripts.prepare_teacher_comparison import prepare_pack


class TeacherPackTests(unittest.TestCase):
    def fixture(self, root):
        (root / "configs").mkdir()
        (root / "prompts").mkdir()
        (root / "prompts/teacher-comparison-v1.txt").write_text(
            (ROOT / "prompts/teacher-comparison-v1.txt").read_text(encoding="utf-8"), encoding="utf-8")
        data = root / "data"
        data.mkdir()
        rows = [{"id": f"train-{i}", "question": f"Question {i}?", "solution": "<<2+3=5>>\n#### 5", "answer": "5"}
                for i in range(12)]
        core.write_jsonl(data / "train.jsonl", rows)
        config = {"model": "student", "dataset": "task"}
        manifest = {**config, "model_revision": "model-sha", "dataset_revision": "data-sha",
                    "dataset_config": "main", "seed": 42, "sizes": {"train": 12},
                    "ids": {"train": [row["id"] for row in rows]},
                    "files": {"train.jsonl": digest(data / "train.jsonl")}}
        core.write_json(data / "manifest.json", manifest)
        core.write_json(root / "configs/pilot.json", config)
        core.write_json(root / "configs/pilot-data-lock.json", core.data_identity(manifest))
        return data, rows

    def test_identical_pack_inputs_and_prompts_are_hashed_and_existing_work_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, rows = self.fixture(root)
            output = root / "pack"
            with patch("scripts.prepare_teacher_comparison.ROOT", root):
                prepare_pack(data, output)
                with self.assertRaisesRegex(ValueError, "already exists"):
                    prepare_pack(data, output)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(core.read_jsonl(output / "inputs.jsonl"), rows[:10])
            self.assertEqual(manifest["question_ids"], [row["id"] for row in rows[:10]])
            self.assertEqual(manifest["expected_candidates_per_teacher"], 80)
            self.assertEqual(len(manifest["prompt_files"]), 10)
            for name, sha in manifest["prompt_files"].items():
                self.assertEqual(digest(output / name), sha)
                text = (output / name).read_text(encoding="utf-8")
                self.assertNotIn("{{problem_json}}", text)
                self.assertIn('"solution": "<<2+3=5>>\\n#### 5"', text)

    def test_changed_split_is_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, _ = self.fixture(root)
            with (data / "train.jsonl").open("a", encoding="utf-8") as target:
                target.write("{}\n")
            with patch("scripts.prepare_teacher_comparison.ROOT", root):
                with self.assertRaisesRegex(ValueError, "Prepared split changed"):
                    prepare_pack(data, root / "pack")
            self.assertFalse((root / "pack").exists())

    def test_different_locked_revision_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, _ = self.fixture(root)
            manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
            manifest["dataset_revision"] = "different"
            (data / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with patch("scripts.prepare_teacher_comparison.ROOT", root):
                with self.assertRaisesRegex(ValueError, "locked pilot"):
                    prepare_pack(data, root / "pack")
            self.assertFalse((root / "pack").exists())


if __name__ == "__main__":
    unittest.main()
