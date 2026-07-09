import unittest
import pickle
import subprocess
import sys
from pathlib import Path


class MMLUFinetuneLocalPathTests(unittest.TestCase):
    def test_cli_accepts_local_data_paths(self):
        from experiment.mmlu import finetune_mmlu

        args = finetune_mmlu.parse_cli_args(
            [
                "--cold_start_dir",
                "experiment/ColdStartData_mmlu",
                "--finetune_data_dir",
                "experiment/FinetuneData_mmlu",
                "--task_split_file",
                "experiment/mmlu/task_split_mmlu.json",
            ]
        )

        self.assertEqual(args.cold_start_dir, "experiment/ColdStartData_mmlu")
        self.assertEqual(args.finetune_data_dir, "experiment/FinetuneData_mmlu")
        self.assertEqual(args.task_split_file, "experiment/mmlu/task_split_mmlu.json")

    def test_default_paths_are_local_workspace_paths(self):
        from experiment.mmlu import finetune_mmlu

        args = finetune_mmlu.parse_cli_args([])

        self.assertNotIn("/root/ARG-Designer", args.cold_start_dir)
        self.assertNotIn("/root/ARG-Designer", args.finetune_data_dir)
        self.assertTrue(args.task_split_file.endswith("experiment/mmlu/task_split_mmlu.json"))

    def test_cli_accepts_cold_start_iteration_alias_and_fixed_output_dir(self):
        from experiment.mmlu import finetune_mmlu

        args = finetune_mmlu.parse_cli_args(
            [
                "--pretrain",
                "--num_iterations",
                "10",
                "--model_output_dir",
                "experiment/mmlu/output/mmlu_arg_base_model_r159",
                "--no_timestamp_output_dir",
            ]
        )

        self.assertTrue(args.pretrain)
        self.assertEqual(args.pretrain_epochs, 10)
        self.assertEqual(
            args.model_output_dir,
            "experiment/mmlu/output/mmlu_arg_base_model_r159",
        )
        self.assertTrue(args.no_timestamp_output_dir)

    def test_script_help_runs_from_repo_root(self):
        repo_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "experiment/mmlu/finetune_mmlu.py", "--help"],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--no_timestamp_output_dir", result.stdout)

    def test_identity_collate_is_picklable_for_worker_dataloader(self):
        from experiment.mmlu import finetune_mmlu

        payload = [{"graph": 1}]
        restored = pickle.loads(pickle.dumps(finetune_mmlu.identity_collate))

        self.assertIs(restored(payload), payload)


if __name__ == "__main__":
    unittest.main()
