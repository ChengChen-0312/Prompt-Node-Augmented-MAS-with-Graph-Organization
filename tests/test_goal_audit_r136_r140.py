import unittest


class GoalAuditR136R140Tests(unittest.TestCase):
    def test_audit_keeps_forwarding_fix_aligned_without_threshold_overfit(self):
        from experiment.aqua.goal_audit_r136_r140 import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["rule"], "r140_goal_audit_r136_r140")
        self.assertEqual(
            summary["status"], "aligned_continue_with_calibration_protocol"
        )
        self.assertEqual(summary["goal_window"], ["R136", "R137", "R138", "R139", "R140"])
        self.assertFalse(summary["drift_detected"])
        self.assertTrue(summary["maintained_update2_alignment"])
        self.assertTrue(summary["maintained_edge_prompt_alignment"])
        self.assertTrue(summary["maintained_robustness_alignment"])
        self.assertTrue(summary["forwarding_gap_fixed"])
        self.assertTrue(summary["clean_gate_still_not_met"])
        self.assertTrue(summary["confidence_calibration_needed"])
        self.assertFalse(summary["threshold_lowering_without_protocol_allowed"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "repair_confidence_calibration_protocol_before_api",
        )
        self.assertEqual(summary["next_goal_audit_due"], "R145")
        self.assertEqual(
            summary["claim_boundary"],
            "five-iteration goal audit and correction, not an accuracy result",
        )


if __name__ == "__main__":
    unittest.main()
