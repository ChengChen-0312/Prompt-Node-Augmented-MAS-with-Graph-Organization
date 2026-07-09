import unittest


class GoalAuditR156R160Tests(unittest.TestCase):
    def test_audit_allows_only_bounded_checkpoint_build_not_transfer(self):
        from experiment.aqua.goal_audit_r156_r160 import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["rule"], "r160_goal_audit_r156_r160")
        self.assertEqual(
            summary["status"],
            "aligned_checkpoint_build_ready_but_no_transfer_evidence",
        )
        self.assertEqual(summary["goal_window"], ["R156", "R157", "R158", "R159", "R160"])
        self.assertFalse(summary["drift_detected"])
        self.assertTrue(summary["maintained_sci_q2_focus"])
        self.assertTrue(summary["maintained_update2_alignment"])
        self.assertTrue(summary["claim_discipline_maintained"])
        self.assertTrue(summary["r156_cold_start_dry_run_ready"])
        self.assertFalse(summary["r156_finetune_dry_run_ready"])
        self.assertTrue(summary["r157_local_path_patch_confirmed"])
        self.assertTrue(summary["r158_finetune_dry_run_ready"])
        self.assertTrue(summary["r159_command_preflight_ready"])
        self.assertFalse(summary["checkpoint_training_run"])
        self.assertFalse(summary["compatible_checkpoint_exists"])
        self.assertFalse(summary["transfer_api_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertTrue(summary["bounded_checkpoint_build_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "r161_bounded_mmlu_checkpoint_build_execution_or_user_budget_gate",
        )
        self.assertEqual(summary["next_goal_audit_due"], "R165")


if __name__ == "__main__":
    unittest.main()
