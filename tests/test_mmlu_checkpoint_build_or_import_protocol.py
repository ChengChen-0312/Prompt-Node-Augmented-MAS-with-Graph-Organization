import unittest


class MMLUCheckpointBuildOrImportProtocolTests(unittest.TestCase):
    def test_protocol_requires_path_patch_or_valid_import_before_transfer(self):
        from experiment.mmlu.checkpoint_build_or_import_protocol import (
            build_checkpoint_protocol_summary,
        )

        summary = build_checkpoint_protocol_summary()

        self.assertEqual(summary["rule"], "r153_mmlu_checkpoint_build_or_import_protocol")
        self.assertTrue(summary["no_api_run"])
        self.assertFalse(summary["compatible_checkpoint_present"])
        self.assertTrue(summary["mmlu_finetune_script_exists"])
        self.assertTrue(summary["mmlu_cold_start_script_exists"])
        self.assertTrue(summary["mmlu_evaluator_exists"])
        self.assertTrue(summary["hardcoded_root_paths_detected"])
        self.assertIsInstance(summary["local_task_split_exists"], bool)
        self.assertTrue(summary["import_route_supported"])
        self.assertEqual(
            summary["build_route"],
            "patch_local_paths_then_coldstart_pretrain_finetune",
        )
        self.assertEqual(
            summary["next_protocol"],
            "r154_local_mmlu_checkpoint_path_patch_or_import_stub",
        )
        self.assertFalse(summary["transfer_api_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_goal_audit_due"], "R155")


if __name__ == "__main__":
    unittest.main()
