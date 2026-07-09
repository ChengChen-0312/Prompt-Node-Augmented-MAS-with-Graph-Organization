import unittest


class TestR337ProspectiveSelectorEvalExpand24(unittest.TestCase):
    def test_expand24_plan_reuses_authorized_smoke_executor(self):
        from experiment.mmlu.r337_prospective_selector_eval_expand24 import build_expand24_plan

        summary = build_expand24_plan()

        self.assertEqual(summary["run_id"], "R337")
        self.assertEqual(summary["tasks"], 24)
        self.assertEqual(summary["records"], 72)
        self.assertEqual(summary["api_calls_planned"], 72)
        self.assertTrue(summary["source_smoke_no_harm"])
        self.assertFalse(summary["api_executed"])
        self.assertEqual(summary["next_required_run"], "R337_execute_with_api_or_R338_goal_audit")


if __name__ == "__main__":
    unittest.main()
