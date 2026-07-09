import unittest


class TestR338GoalAuditAfterProspectiveEval(unittest.TestCase):
    def test_goal_audit_blocks_prospective_improvement_claim_after_no_harm_tie(self):
        from experiment.mmlu.r338_goal_audit_after_prospective_eval import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R338")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R333", "R334", "R335", "R336", "R337"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["prospective_eval_completed"])
        self.assertFalse(summary["claim_permissions"]["prospective_selector_improvement_claim_allowed"])
        self.assertTrue(summary["claim_permissions"]["prospective_selector_no_harm_claim_allowed"])
        self.assertTrue(summary["claim_permissions"]["plain_requery_harm_control_allowed"])
        self.assertFalse(summary["claim_permissions"]["sci_q2_ready"])
        self.assertEqual(summary["course_correction"][0], "Analyze why the prospective selector does not switch before spending more API.")
        self.assertEqual(summary["next_required_run"], "R339_selector_non_switch_failure_analysis")


if __name__ == "__main__":
    unittest.main()
