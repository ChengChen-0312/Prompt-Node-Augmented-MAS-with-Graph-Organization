import unittest


class TestR380OptionBindingFreshEvalApiExecution(unittest.TestCase):
    def test_api_execution_plan_is_leakage_checked_and_uses_r373_gate(self):
        from experiment.mmlu.r380_option_binding_fresh_eval_api_execution import build_api_execution_plan

        summary = build_api_execution_plan()

        self.assertEqual(summary["run_id"], "R380")
        self.assertEqual(summary["tasks"], 24)
        self.assertEqual(summary["api_calls_planned"], 48)
        self.assertEqual(summary["policy_model"], "R373_source_invariant_gate_with_r369_hard_negatives")
        self.assertEqual(summary["policy_threshold"], 0.7)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["api_executed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R380_execute_with_api_or_R381_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
