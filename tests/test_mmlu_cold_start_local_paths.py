import unittest
import os
import subprocess
import sys
from pathlib import Path


class MMLUColdStartLocalPathTests(unittest.TestCase):
    def test_cli_accepts_local_output_split_reuse_and_seed(self):
        from experiment.mmlu import cold_start_mmlu

        args = cold_start_mmlu.parse_args(
            [
                "--output_dir",
                "experiment/ColdStartData_mmlu",
                "--task_split_file",
                "experiment/mmlu/task_split_mmlu.json",
                "--records_csv",
                "experiment/mmlu/run_logs/r161_records.csv",
                "--reuse_task_split",
                "--seed",
                "42",
            ]
        )

        self.assertEqual(args.output_dir, "experiment/ColdStartData_mmlu")
        self.assertEqual(args.task_split_file, "experiment/mmlu/task_split_mmlu.json")
        self.assertEqual(args.records_csv, "experiment/mmlu/run_logs/r161_records.csv")
        self.assertTrue(args.reuse_task_split)
        self.assertEqual(args.seed, 42)

    def test_default_paths_are_local_workspace_paths(self):
        from experiment.mmlu import cold_start_mmlu

        args = cold_start_mmlu.parse_args([])

        self.assertTrue(args.output_dir.endswith("experiment/ColdStartData_mmlu"))
        self.assertTrue(args.task_split_file.endswith("experiment/mmlu/task_split_mmlu.json"))
        self.assertTrue(args.records_csv.endswith("experiment/mmlu/run_logs/cold_start_records.csv"))

    def test_script_help_runs_from_repo_root(self):
        repo_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "experiment/mmlu/cold_start_mmlu.py", "--help"],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--reuse_task_split", result.stdout)

    def test_local_mmlu_data_root_skips_download(self):
        from experiment.mmlu import cold_start_mmlu

        repo_parent = Path(__file__).resolve().parents[2]
        data_root = repo_parent / "OpenG-MAS_benchmark_code_release" / "datasets" / "MMLU"
        old_root = os.environ.get("MMLU_DATA_ROOT")
        os.environ["MMLU_DATA_ROOT"] = str(data_root)
        try:
            self.assertTrue(cold_start_mmlu.local_mmlu_data_available())
        finally:
            if old_root is None:
                os.environ.pop("MMLU_DATA_ROOT", None)
            else:
                os.environ["MMLU_DATA_ROOT"] = old_root


if __name__ == "__main__":
    unittest.main()
