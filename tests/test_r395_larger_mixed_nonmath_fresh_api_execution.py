import unittest


class TestR395LargerMixedNonmathFreshApiExecution(unittest.TestCase):
    def test_api_execution_plan_uses_retrained_gate_and_is_leakage_checked(self):
        from experiment.mmlu.r395_larger_mixed_nonmath_fresh_api_execution import build_api_execution_plan

        summary = build_api_execution_plan()

        self.assertEqual(summary["run_id"], "R395")
        self.assertEqual(summary["tasks"], 48)
        self.assertEqual(summary["api_calls_planned"], 96)
        self.assertEqual(summary["policy_model"], "R392_weighted_mixed_nonmath_gate")
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["api_executed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R395_execute_with_api_or_R396_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
