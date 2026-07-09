import unittest


class TestR320GoalAuditAfterAblations(unittest.TestCase):
    def test_goal_audit_keeps_ablation_results_inside_sci_q2_boundary(self):
        from experiment.mmlu.r320_goal_audit_after_ablations import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R320")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R315", "R316", "R317", "R318", "R319"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["priority_ablations_completed"])
        self.assertTrue(summary["goal_alignment"]["promptedge_text_validated"])
        self.assertTrue(summary["goal_alignment"]["symbolic_and_nonmath_contributions_separated"])
        self.assertTrue(summary["claim_permissions"]["aqua_clean_improvement_allowed"])
        self.assertTrue(summary["claim_permissions"]["mmlu_stem_improvement_allowed"])
        self.assertTrue(summary["claim_permissions"]["mmlu_nonstem_no_harm_allowed"])
        self.assertFalse(summary["claim_permissions"]["mmlu_nonstem_improvement_allowed"])
        self.assertFalse(summary["claim_permissions"]["broad_general_promptnode_claim_allowed"])
        self.assertFalse(summary["claim_permissions"]["training_authorized"])
        self.assertFalse(summary["claim_permissions"]["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R321_paper_evidence_table_and_training_gate")


if __name__ == "__main__":
    unittest.main()
