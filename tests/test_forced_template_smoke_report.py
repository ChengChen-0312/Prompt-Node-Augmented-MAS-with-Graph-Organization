import unittest


class ForcedTemplateSmokeReportTests(unittest.TestCase):
    def test_build_smoke_summary_captures_router_status_and_costs(self):
        from experiment.aqua.forced_template_smoke_report import build_smoke_summary

        summary = build_smoke_summary()

        self.assertEqual(summary["rule"], "r084_forced_template_smoke_report")
        self.assertEqual(summary["num_smoke_runs"], 4)
        self.assertEqual(summary["solved_runs"], 1)
        self.assertEqual(summary["promptnode_graph_runs"], 4)
        self.assertEqual(summary["router_status_counts"]["EXACT_MATCH"], 2)
        self.assertEqual(summary["router_status_counts"]["NO_EXACT_OPTION"], 2)
        self.assertEqual(summary["task_outcomes"]["task_56"]["best_result"], "1/1")
        self.assertEqual(summary["task_outcomes"]["task_114"]["best_result"], "0/3")
        self.assertIn("smoke-only", summary["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
