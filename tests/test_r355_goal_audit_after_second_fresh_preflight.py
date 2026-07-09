import unittest


class TestR355GoalAuditAfterSecondFreshPreflight(unittest.TestCase):
    def test_goal_audit_redirects_from_hand_templates_to_learned_graph_policy(self):
        from experiment.mmlu.r355_goal_audit_after_second_fresh_preflight import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R355")
        self.assertEqual(summary["early_goal_audit_reason"], "second_fresh_zero_coverage")
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["r352_dev_coverage_positive"])
        self.assertTrue(summary["goal_alignment"]["r354_fresh_coverage_zero"])
        self.assertTrue(summary["goal_alignment"]["local_template_path_failed_as_general_strategy"])
        self.assertFalse(summary["claim_permissions"]["hand_template_expansion_allowed_as_primary_path"])
        self.assertTrue(summary["claim_permissions"]["learned_graph_policy_design_required"])
        self.assertFalse(summary["claim_permissions"]["api_execution_allowed_now"])
        self.assertEqual(summary["course_correction"][0], "Stop hand-expanding deterministic templates as the primary path.")
        self.assertEqual(summary["next_required_run"], "R356_learned_graph_policy_promptnode_design")


if __name__ == "__main__":
    unittest.main()
