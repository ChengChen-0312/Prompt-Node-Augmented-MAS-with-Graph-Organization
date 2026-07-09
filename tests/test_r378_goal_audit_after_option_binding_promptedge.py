import unittest


class TestR378GoalAuditAfterOptionBindingPromptEdge(unittest.TestCase):
    def test_goal_audit_keeps_claim_boundary_and_authorizes_fresh_preflight(self):
        from experiment.mmlu.r378_goal_audit_after_option_binding_promptedge import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R378")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R373", "R374", "R375", "R376", "R377"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["fresh_history_eval_no_harm"])
        self.assertFalse(summary["goal_alignment"]["fresh_history_eval_positive"])
        self.assertTrue(summary["goal_alignment"]["option_binding_replay_positive"])
        self.assertTrue(summary["goal_alignment"]["overclaiming_blocked"])
        self.assertTrue(summary["claim_permissions"]["fresh_preflight_allowed_next"])
        self.assertFalse(summary["claim_permissions"]["api_execution_allowed_now"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R379_option_binding_fresh_eval_preflight")


if __name__ == "__main__":
    unittest.main()
