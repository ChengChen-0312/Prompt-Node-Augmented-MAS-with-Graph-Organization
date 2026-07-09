import unittest


class MMLUCheckpointBuildDryRunAfterPathPatchTests(unittest.TestCase):
    def test_after_patch_finetune_dry_run_is_ready_without_training(self):
        from experiment.mmlu.checkpoint_build_dry_run_after_path_patch import (
            build_after_patch_summary,
        )

        summary = build_after_patch_summary()

        self.assertEqual(
            summary["rule"],
            "r158_mmlu_checkpoint_build_dry_run_after_path_patch",
        )
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["r157_path_patch_confirmed"])
        self.assertTrue(summary["mmlu_data_root_exists"])
        self.assertTrue(summary["task_split_exists"])
        self.assertTrue(summary["split_indices_valid"])
        self.assertTrue(summary["cold_start_dry_run_ready"])
        self.assertTrue(summary["finetune_dry_run_ready"])
        self.assertEqual(summary["finetune_blockers"], [])
        self.assertFalse(summary["checkpoint_training_run"])
        self.assertFalse(summary["compatible_checkpoint_exists"])
        self.assertFalse(summary["transfer_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "r159_mmlu_checkpoint_build_command_preflight",
        )


if __name__ == "__main__":
    unittest.main()
