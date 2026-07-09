import unittest


class MMLUFinetuneLocalPathPatchReportTests(unittest.TestCase):
    def test_report_marks_path_patch_without_training_or_transfer(self):
        from experiment.mmlu.finetune_local_path_patch_report import build_patch_summary

        summary = build_patch_summary()

        self.assertEqual(summary["rule"], "r157_mmlu_finetune_local_path_patch")
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["parse_cli_accepts_local_paths"])
        self.assertTrue(summary["default_paths_are_local"])
        self.assertTrue(summary["hardcoded_root_argdesigner_removed"])
        self.assertFalse(summary["checkpoint_training_run"])
        self.assertFalse(summary["transfer_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "r158_mmlu_checkpoint_build_dry_run_after_path_patch",
        )


if __name__ == "__main__":
    unittest.main()
