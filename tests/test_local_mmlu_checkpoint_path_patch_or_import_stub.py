import unittest


class LocalMMLUCheckpointPathPatchOrImportStubTests(unittest.TestCase):
    def test_stub_plans_local_split_and_keeps_transfer_blocked(self):
        from experiment.mmlu.local_checkpoint_path_patch_or_import_stub import (
            build_local_patch_summary,
        )

        summary = build_local_patch_summary(write_split=False)

        self.assertEqual(
            summary["rule"],
            "r154_local_mmlu_checkpoint_path_patch_or_import_stub",
        )
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["dataset_env_patch_available"])
        self.assertTrue(summary["local_mmlu_root_exists"])
        self.assertGreater(summary["local_dev_rows"], 0)
        self.assertEqual(summary["planned_base_task_count"], 16)
        self.assertEqual(summary["planned_finetune_task_count"], 24)
        self.assertFalse(summary["task_split_written"])
        self.assertTrue(summary["import_stub_available"])
        self.assertFalse(summary["compatible_checkpoint_imported"])
        self.assertFalse(summary["transfer_api_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_protocol"], "r155_goal_audit_r151_r155")


if __name__ == "__main__":
    unittest.main()
