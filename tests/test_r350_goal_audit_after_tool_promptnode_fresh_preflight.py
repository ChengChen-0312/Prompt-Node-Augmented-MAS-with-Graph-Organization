import unittest


class TestR350GoalAuditAfterToolPromptnodeFreshPreflight(unittest.TestCase):
    def test_goal_audit_blocks_fresh_api_when_frozen_tool_policy_has_zero_coverage(self):
        from experiment.mmlu.r350_goal_audit_after_tool_promptnode_fresh_preflight import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R350")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R345", "R346", "R347", "R348", "R349"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["r347_replay_positive"])
        self.assertTrue(summary["goal_alignment"]["r349_fresh_split_ready"])
        self.assertTrue(summary["goal_alignment"]["fresh_tool_coverage_gap_detected"])
        self.assertFalse(summary["claim_permissions"]["fresh_api_execution_allowed_now"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["course_correction"][0], "Do not run fresh API while the frozen tool policy forwards zero candidates.")
        self.assertEqual(summary["next_required_run"], "R351_fresh_coverage_promptnode_expansion_design")


if __name__ == "__main__":
    unittest.main()
