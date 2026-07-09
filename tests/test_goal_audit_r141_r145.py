import unittest


class GoalAuditR141R145Tests(unittest.TestCase):
    def test_audit_allows_only_bounded_api_after_calibration_presmoke(self):
        from experiment.aqua.goal_audit_r141_r145 import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["rule"], "r145_goal_audit_r141_r145")
        self.assertEqual(
            summary["status"], "aligned_allow_bounded_calibrated_smoke"
        )
        self.assertEqual(summary["goal_window"], ["R141", "R142", "R143", "R144", "R145"])
        self.assertFalse(summary["drift_detected"])
        self.assertTrue(summary["maintained_update2_alignment"])
        self.assertTrue(summary["maintained_edge_prompt_alignment"])
        self.assertTrue(summary["maintained_robustness_alignment"])
        self.assertTrue(summary["calibration_no_tail34_training"])
        self.assertTrue(summary["r143_offline_gate_passed"])
        self.assertTrue(summary["r144_decision_method_registered"])
        self.assertTrue(summary["r144_goal_audit_required_before_api"])
        self.assertTrue(summary["bounded_api_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_protocol"], "r146_bounded_calibrated_repair_api_smoke")
        self.assertEqual(summary["next_goal_audit_due"], "R150")


if __name__ == "__main__":
    unittest.main()
