import unittest


class GoalAuditR151R155Tests(unittest.TestCase):
    def test_audit_keeps_transfer_engineering_aligned_but_not_ready(self):
        from experiment.aqua.goal_audit_r151_r155 import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["rule"], "r155_goal_audit_r151_r155")
        self.assertEqual(
            summary["status"],
            "aligned_transfer_engineering_not_sci_q2_ready",
        )
        self.assertEqual(summary["goal_window"], ["R151", "R152", "R153", "R154", "R155"])
        self.assertFalse(summary["drift_detected"])
        self.assertTrue(summary["maintained_sci_q2_focus"])
        self.assertTrue(summary["r151_plan_only"])
        self.assertFalse(summary["r152_transfer_branch_allowed"])
        self.assertFalse(summary["r152_independent_same_method_aqua_replicate_ready"])
        self.assertFalse(summary["r153_compatible_checkpoint_present"])
        self.assertTrue(summary["r154_dataset_env_patch_available"])
        self.assertTrue(summary["r154_task_split_written"])
        self.assertFalse(summary["r154_compatible_checkpoint_imported"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertTrue(summary["checkpoint_build_preflight_allowed_next"])
        self.assertFalse(summary["transfer_api_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "r156_mmlu_checkpoint_build_dry_run_or_import_validation",
        )
        self.assertEqual(summary["next_goal_audit_due"], "R160")


if __name__ == "__main__":
    unittest.main()
