import unittest


class TestR366GoalAuditAfterSourceInvariantFreshEval(unittest.TestCase):
    def test_goal_audit_keeps_no_harm_gain_but_blocks_sci_q2_claim(self):
        from experiment.mmlu.r366_goal_audit_after_source_invariant_fresh_eval import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R366")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R362", "R363", "R364", "R365"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["fresh_eval_positive_no_harm"])
        self.assertTrue(summary["goal_alignment"]["gain_insufficient_for_sci_q2"])
        self.assertTrue(summary["goal_alignment"]["candidate_quality_bottleneck_identified"])
        self.assertTrue(summary["claim_permissions"]["fresh_positive_delta_no_harm_claim_allowed"])
        self.assertFalse(summary["claim_permissions"]["api_execution_allowed_now"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R367_adversarial_candidate_verifier_design")


if __name__ == "__main__":
    unittest.main()
