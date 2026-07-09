import unittest


class TestR383PlainRequeryControlApiExecution(unittest.TestCase):
    def test_api_execution_plan_is_leakage_checked(self):
        from experiment.mmlu.r383_plain_requery_control_api_execution import build_api_execution_plan

        summary = build_api_execution_plan()

        self.assertEqual(summary["run_id"], "R383")
        self.assertEqual(summary["tasks"], 24)
        self.assertEqual(summary["api_calls_planned"], 24)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["api_executed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R383_execute_with_api_or_R384_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
