import unittest


class TestR424MmluStemCostProbeApiExecution(unittest.TestCase):
    def test_plan_is_available_without_api_execution(self):
        from experiment.mmlu.r424_mmlu_stem_cost_probe_api_execution import build_api_execution_plan

        plan = build_api_execution_plan()

        self.assertEqual(plan["run_id"], "R424")
        self.assertEqual(plan["tasks"], 12)
        self.assertEqual(plan["api_calls_planned"], 24)
        self.assertTrue(plan["leakage_pass"])
        self.assertFalse(plan["api_executed"])
        self.assertEqual(plan["next_required_run"], "R424_execute_with_api_or_R425_analyze_cost_probe")


if __name__ == "__main__":
    unittest.main()
