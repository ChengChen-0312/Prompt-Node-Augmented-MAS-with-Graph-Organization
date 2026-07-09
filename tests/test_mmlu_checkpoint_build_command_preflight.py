import unittest


class MMLUCheckpointBuildCommandPreflightTests(unittest.TestCase):
    def test_preflight_defines_bounded_build_command_without_api(self):
        from experiment.mmlu.checkpoint_build_command_preflight import (
            build_command_preflight_summary,
        )

        summary = build_command_preflight_summary()

        self.assertEqual(summary["rule"], "r159_mmlu_checkpoint_build_command_preflight")
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["r158_finetune_dry_run_ready"])
        self.assertEqual(summary["llm_name"], "gpt-4o-2024-08-06")
        self.assertEqual(summary["num_iterations"], 10)
        self.assertEqual(summary["batch_size"], 4)
        self.assertEqual(summary["planned_training_sample_count"], 40)
        self.assertTrue(summary["uses_local_mmlu_data_root"])
        self.assertIn("--pretrain", summary["build_command"])
        self.assertIn("--no_timestamp_output_dir", summary["build_command"])
        self.assertIn("--task_split_file", summary["build_command"])
        self.assertFalse(summary["checkpoint_training_run"])
        self.assertFalse(summary["transfer_api_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_protocol"], "r160_goal_audit_r156_r160")


if __name__ == "__main__":
    unittest.main()
