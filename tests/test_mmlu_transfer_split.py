import json
import os
import subprocess
import sys
import unittest


LOCAL_MMLU_TEST_JSONL = (
    "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/"
    "datasets/MMLU/test.jsonl"
)


def _raw_record(task_id, subject, answer="B", source_index=0):
    return {
        "id": task_id,
        "question": (
            f"Solve {task_id}?\n"
            "Option A: alpha\n"
            "Option B: beta\n"
            "Option C: gamma\n"
            "Option D: delta"
        ),
        "answer": answer,
        "metadata": {
            "subject": subject,
            "choices": [
                ["A", "alpha"],
                ["B", "beta"],
                ["C", "gamma"],
                ["D", "delta"],
            ],
            "source_file": f"datasets/MMLU/test/{subject}_test.csv",
            "source_file_format": "mmlu_csv",
            "source_index": source_index,
        },
    }


class MMLUTransferSplitTests(unittest.TestCase):
    def test_normalize_jsonl_record_preserves_option_binding(self):
        from experiment.mmlu.transfer_split import normalize_jsonl_record

        record = _raw_record(
            "MMLU-college_mathematics_test-7",
            "college_mathematics",
            answer="C",
            source_index=7,
        )

        normalized = normalize_jsonl_record(record)

        self.assertEqual(normalized["task_id"], "MMLU-college_mathematics_test-7")
        self.assertEqual(normalized["subject"], "college_mathematics")
        self.assertEqual(normalized["answer"], "C")
        self.assertEqual(normalized["option_labels"], ["A", "B", "C", "D"])
        self.assertEqual(normalized["options"][1], ["B", "beta"])
        self.assertEqual(normalized["source_index"], 7)
        self.assertIn("Option A: alpha", normalized["question"])
        self.assertIn("Option D: delta", normalized["question"])

    def test_build_transfer_split_filters_stem_subjects_and_round_robins(self):
        from experiment.mmlu.transfer_split import build_transfer_split

        records = [
            _raw_record("math-2", "college_mathematics", source_index=2),
            _raw_record("law-0", "professional_law", source_index=0),
            _raw_record("algebra-0", "abstract_algebra", source_index=0),
            _raw_record("math-0", "college_mathematics", source_index=0),
            _raw_record("math-1", "college_mathematics", source_index=1),
        ]

        selected, summary = build_transfer_split(
            records,
            subjects=["college_mathematics", "abstract_algebra"],
            max_per_subject=2,
            limit=3,
        )

        self.assertEqual(
            [item["task_id"] for item in selected],
            ["math-0", "algebra-0", "math-1"],
        )
        self.assertEqual(summary["total_tasks"], 3)
        self.assertEqual(
            summary["subject_counts"],
            {"college_mathematics": 2, "abstract_algebra": 1},
        )
        self.assertNotIn("professional_law", summary["subject_counts"])

    def test_real_local_mmlu_jsonl_builds_stem100_split(self):
        if not os.path.exists(LOCAL_MMLU_TEST_JSONL):
            self.skipTest("Local MMLU test.jsonl is not present in this workspace")

        from experiment.mmlu.transfer_split import (
            DEFAULT_STEM_SUBJECTS,
            build_transfer_split,
            load_jsonl_records,
        )

        records = load_jsonl_records(LOCAL_MMLU_TEST_JSONL)
        selected, summary = build_transfer_split(
            records,
            subjects=DEFAULT_STEM_SUBJECTS,
            max_per_subject=12,
            limit=100,
        )

        task_ids = [item["task_id"] for item in selected]
        self.assertEqual(len(selected), 100)
        self.assertEqual(len(task_ids), len(set(task_ids)))
        self.assertEqual(summary["total_tasks"], 100)
        self.assertEqual(summary["subject_count"], 15)
        self.assertEqual(summary["option_labels"], ["A", "B", "C", "D"])
        self.assertTrue(all(item["answer"] in {"A", "B", "C", "D"} for item in selected))
        self.assertTrue(all(item["subject"] in DEFAULT_STEM_SUBJECTS for item in selected))
        self.assertTrue(all(count <= 12 for count in summary["subject_counts"].values()))

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/mmlu/transfer_split.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
