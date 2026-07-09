import unittest


class TestR353FreshEvalAfterCoverageExpansionDesign(unittest.TestCase):
    def test_design_freezes_expanded_policy_and_requires_new_fresh_split(self):
        from experiment.mmlu.r353_fresh_eval_after_coverage_expansion_design import build_fresh_eval_design

        summary = build_fresh_eval_design()

        self.assertEqual(summary["run_id"], "R353")
        self.assertEqual(summary["policy_frozen_after_run"], "R352")
        self.assertIn("R349", summary["exclude_prior_runs"])
        self.assertIn("R352", summary["exclude_prior_runs"])
        self.assertEqual(summary["fresh_task_plan"], {"mmlu_nonstem": 24, "mmlu_stem": 24})
        self.assertEqual(summary["planned_variants"], ["arg_baseline_direct_api", "expanded_tool_promptnode_local", "hybrid_arg_plus_expanded_tool"])
        self.assertEqual(summary["api_calls_planned"], 48)
        self.assertTrue(summary["preflight_required_next"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R354_fresh_eval_after_coverage_expansion_preflight")


if __name__ == "__main__":
    unittest.main()
