import unittest


class GoalAuditR146R150Tests(unittest.TestCase):
    def test_audit_keeps_direction_aligned_but_blocks_sci_ready_claim(self):
        from experiment.aqua.goal_audit_r146_r150 import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["rule"], "r150_goal_audit_r146_r150")
        self.assertEqual(summary["goal_window"], ["R146", "R147", "R148", "R149", "R150"])
        self.assertEqual(summary["status"], "aligned_but_not_sci_q2_ready")
        self.assertFalse(summary["drift_detected"])
        self.assertTrue(summary["r146_smoke_gate_passed"])
        self.assertEqual(summary["r147_selected_accuracy"], "30/34")
        self.assertFalse(summary["r148_statistically_significant_at_0_05"])
        self.assertFalse(summary["r148_cost_normalized_superiority_supported"])
        self.assertFalse(summary["r149_transfer_branch_allowed"])
        self.assertTrue(summary["r149_family_replicate_claim_allowed"])
        self.assertTrue(summary["maintained_update2_alignment"])
        self.assertTrue(summary["maintained_edge_prompt_alignment"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_goal_audit_due"], "R155")
        self.assertEqual(
            summary["next_protocol"],
            "r151_sci_q2_evidence_gap_plan_before_more_api",
        )


if __name__ == "__main__":
    unittest.main()
