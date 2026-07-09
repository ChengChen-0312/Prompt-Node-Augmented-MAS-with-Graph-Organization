import unittest


class Rank5HighFaninSelectorSmokeReportTests(unittest.TestCase):
    def test_report_uses_r127_switch_plan_and_fallback_guards(self):
        from experiment.aqua.rank5_high_fanin_selector_smoke_report import (
            build_rank5_high_fanin_selector_smoke_summary,
            build_evaluate_command,
            write_switch_task_split,
        )

        payload = write_switch_task_split()
        self.assertEqual(payload["test_indices"], [108, 250])
        self.assertIn("--forced_template_candidate_rank 5", build_evaluate_command())

        summary = build_rank5_high_fanin_selector_smoke_summary(
            forced_jsonl="experiment/aqua/aqua_tail34_r106_rank5_regression_smoke_results.jsonl",
            forced_summary_jsonl="experiment/aqua/res_logs/aqua_tail34_r106_rank5_regression_smoke_summary.jsonl",
        )

        self.assertEqual(summary["rule"], "r128_rank5_high_fanin_selector_smoke")
        self.assertEqual(summary["baseline_accuracy"], "2/4")
        self.assertEqual(summary["selected_accuracy"], "4/4")
        self.assertEqual(summary["switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["fallback_tasks"], ["task_8", "task_188"])
        self.assertEqual(summary["selected_template_ranks"], {"task_108": 5, "task_250": 5})
        self.assertEqual(summary["promptnode_graph_evidence_on_switches"], "2/2")
        self.assertEqual(summary["switch_update2_metadata"], "2/2")
        self.assertEqual(summary["high_fanin_memory_bridge_on_switches"], "2/2")
        self.assertEqual(summary["fix_harm"], "2/0")
        self.assertEqual(summary["clean_fix_harm"], "1/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["selector_input_field_violations"], 0)
        self.assertTrue(summary["smoke_gate_passed"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["claim_boundary"],
            "same-four-task rank5 high-fanin selector smoke; broad claims require a fresh R128 API run and separate audit",
        )


if __name__ == "__main__":
    unittest.main()
