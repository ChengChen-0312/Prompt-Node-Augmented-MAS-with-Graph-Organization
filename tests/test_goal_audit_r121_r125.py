import unittest


class GoalAuditR121R125Tests(unittest.TestCase):
    def test_audit_corrects_rank1_template_path_after_evidence_recovery(self):
        from experiment.aqua.goal_audit_r121_r125 import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["rule"], "r125_goal_audit_r121_r125")
        self.assertEqual(summary["status"], "aligned_after_correction")
        self.assertEqual(summary["goal_window"], ["R121", "R122", "R123", "R124", "R125"])
        self.assertTrue(summary["drift_detected"])
        self.assertEqual(
            summary["drift_type"],
            "rank1_explicit_template_path_restores_update2_evidence_but_fails_clean_fix_gate",
        )
        self.assertEqual(summary["r124_selected_accuracy"], "3/4")
        self.assertEqual(summary["r124_baseline_accuracy"], "2/4")
        self.assertEqual(summary["r124_clean_fix_harm"], "0/0")
        self.assertEqual(summary["r124_promptnode_graph_evidence_on_switches"], "2/2")
        self.assertEqual(summary["r124_switch_update2_metadata"], "2/2")
        self.assertFalse(summary["r124_smoke_gate_passed"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "train_or_select_clean_fix_graph_policy_before_smoke",
        )
        self.assertIn("task_250", summary["required_clean_recovery_targets"])
        self.assertEqual(
            summary["claim_boundary"],
            "five-iteration goal audit and correction, not an accuracy result",
        )


if __name__ == "__main__":
    unittest.main()
