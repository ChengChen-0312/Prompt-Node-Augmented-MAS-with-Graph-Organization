import unittest


class TestR389MixedNonmathOptionBindingApiExecution(unittest.TestCase):
    def test_api_execution_plan_is_leakage_checked(self):
        from experiment.mmlu.r389_mixed_nonmath_option_binding_api_execution import build_api_execution_plan

        summary = build_api_execution_plan()

        self.assertEqual(summary["run_id"], "R389")
        self.assertEqual(summary["tasks"], 24)
        self.assertEqual(summary["api_calls_planned"], 48)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["api_executed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R389_execute_with_api_or_R390_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
