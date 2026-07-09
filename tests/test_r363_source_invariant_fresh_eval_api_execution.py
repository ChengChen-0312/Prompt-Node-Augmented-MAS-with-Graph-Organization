import unittest


class TestR363SourceInvariantFreshEvalApiExecution(unittest.TestCase):
    def test_api_execution_plan_is_leakage_checked_and_uses_source_invariant_gate(self):
        from experiment.mmlu.r363_source_invariant_fresh_eval_api_execution import build_api_execution_plan

        summary = build_api_execution_plan()

        self.assertEqual(summary["run_id"], "R363")
        self.assertEqual(summary["tasks"], 48)
        self.assertEqual(summary["api_calls_planned"], 96)
        self.assertEqual(summary["policy_model"], "R360_source_invariant_graph_policy")
        self.assertEqual(summary["policy_threshold"], 0.7)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["api_executed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R363_execute_with_api_or_R364_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
