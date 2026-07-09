import unittest


class TestR361GoalAuditAfterSourceInvariantPolicy(unittest.TestCase):
    def test_goal_audit_authorizes_fresh_preflight_but_not_api_or_paper_claim(self):
        from experiment.mmlu.r361_goal_audit_after_source_invariant_policy import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R361")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R356", "R357", "R358", "R359", "R360"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["source_shortcut_detected_and_corrected"])
        self.assertTrue(summary["goal_alignment"]["source_invariant_gate_ready_for_preflight"])
        self.assertTrue(summary["claim_permissions"]["fresh_eval_preflight_allowed"])
        self.assertFalse(summary["claim_permissions"]["api_execution_allowed_now"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R362_source_invariant_fresh_eval_preflight")


if __name__ == "__main__":
    unittest.main()
