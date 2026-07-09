import unittest


class TestR344GoalAuditAfterCandidateGeneratorProbe(unittest.TestCase):
    def test_goal_audit_redirects_to_tool_backed_general_promptnodes(self):
        from experiment.mmlu.r344_goal_audit_after_candidate_generator_probe import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R344")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R339", "R340", "R341", "R342", "R343"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["arg_baseline_preserved"])
        self.assertTrue(summary["goal_alignment"]["promptnode_not_dataset_patch"])
        self.assertTrue(summary["goal_alignment"]["same_prompt_only_path_blocked"])
        self.assertTrue(summary["claim_permissions"]["tool_backed_promptnode_design_allowed"])
        self.assertFalse(summary["claim_permissions"]["more_api_same_prompt_design_allowed"])
        self.assertFalse(summary["claim_permissions"]["broad_general_promptnode_claim_allowed"])
        self.assertEqual(summary["course_correction"][0], "Replace prompt-only answer-bearing verifier expansion with tool-backed or symbolic PromptNodes.")
        self.assertEqual(summary["next_required_run"], "R345_tool_backed_promptnode_verifier_design")


if __name__ == "__main__":
    unittest.main()
