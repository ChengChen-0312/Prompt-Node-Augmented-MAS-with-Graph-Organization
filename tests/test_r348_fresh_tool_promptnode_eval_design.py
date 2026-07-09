import unittest


class TestR348FreshToolPromptnodeEvalDesign(unittest.TestCase):
    def test_design_freezes_policy_and_requires_fresh_stem_and_nonstem_splits(self):
        from experiment.mmlu.r348_fresh_tool_promptnode_eval_design import build_fresh_eval_design

        summary = build_fresh_eval_design()

        self.assertEqual(summary["run_id"], "R348")
        self.assertEqual(summary["policy_frozen_after_run"], "R347")
        self.assertEqual(summary["fresh_task_plan"], {"mmlu_nonstem": 24, "mmlu_stem": 24})
        self.assertIn("R334", summary["exclude_prior_runs"])
        self.assertIn("R337", summary["exclude_prior_runs"])
        self.assertEqual(summary["planned_variants"], ["arg_baseline_direct_api", "frozen_tool_promptnode_local", "hybrid_arg_plus_tool"])
        self.assertEqual(summary["api_calls_planned"], 48)
        self.assertTrue(summary["leakage_preflight_required_next"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R349_fresh_tool_promptnode_eval_preflight")


if __name__ == "__main__":
    unittest.main()
