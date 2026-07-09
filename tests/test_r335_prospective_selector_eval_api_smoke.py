import unittest


class TestR335ProspectiveSelectorEvalApiSmoke(unittest.TestCase):
    def test_dry_run_plans_bounded_api_smoke_with_runtime_baseline_injection(self):
        from experiment.mmlu.r335_prospective_selector_eval_api_smoke import build_api_smoke_plan

        summary = build_api_smoke_plan(limit_tasks=6)

        self.assertEqual(summary["run_id"], "R335")
        self.assertEqual(summary["tasks"], 6)
        self.assertEqual(summary["records"], 18)
        self.assertEqual(summary["api_calls_planned"], 18)
        self.assertTrue(summary["runtime_baseline_injection_required"])
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["api_executed"])
        self.assertEqual(summary["next_required_run"], "R335_execute_with_api_or_R336_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
