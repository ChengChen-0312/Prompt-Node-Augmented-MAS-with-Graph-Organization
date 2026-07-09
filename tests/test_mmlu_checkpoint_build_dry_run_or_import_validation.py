import unittest


class MMLUCheckpointBuildDryRunOrImportValidationTests(unittest.TestCase):
    def test_dry_run_validates_split_but_keeps_finetune_blocked(self):
        from experiment.mmlu.checkpoint_build_dry_run_or_import_validation import (
            build_dry_run_summary,
        )

        summary = build_dry_run_summary()

        self.assertEqual(
            summary["rule"],
            "r156_mmlu_checkpoint_build_dry_run_or_import_validation",
        )
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["mmlu_data_root_exists"])
        self.assertTrue(summary["task_split_exists"])
        self.assertTrue(summary["split_indices_valid"])
        self.assertTrue(summary["cold_start_dry_run_ready"])
        self.assertFalse(summary["finetune_dry_run_ready"])
        self.assertTrue(summary["import_validation_ready"])
        self.assertFalse(summary["compatible_checkpoint_imported"])
        self.assertFalse(summary["transfer_api_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_protocol"], "r157_mmlu_finetune_local_path_patch")


if __name__ == "__main__":
    unittest.main()
