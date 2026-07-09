import unittest


class BadExactGateForcedTail34ReportTests(unittest.TestCase):
    def test_report_builder_replays_frozen_gate_on_forced_template_records(self):
        from experiment.aqua.bad_exact_gate_forced_tail34_report import (
            build_forced_tail34_gate_summary,
        )

        forced_runs = [
            (
                "experiment/aqua/aqua_tail34_r084_forced_template_rank1_task56_smoke_results.jsonl",
                "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank1_task56_smoke_summary.jsonl",
            ),
            (
                "experiment/aqua/aqua_tail34_r085_forced_template_rank1_task188_smoke_results.jsonl",
                "experiment/aqua/res_logs/aqua_tail34_r085_forced_template_rank1_task188_smoke_summary.jsonl",
            ),
            (
                "experiment/aqua/aqua_tail34_r085_forced_template_rank1_task8_smoke_results.jsonl",
                "experiment/aqua/res_logs/aqua_tail34_r085_forced_template_rank1_task8_smoke_summary.jsonl",
            ),
            (
                "experiment/aqua/aqua_tail34_r084_forced_template_rank1_router_hardened_smoke1_results.jsonl",
                "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank1_router_hardened_smoke1_summary.jsonl",
            ),
            (
                "experiment/aqua/aqua_tail34_r090_forced_template_rank1_task108_smoke_results.jsonl",
                "experiment/aqua/res_logs/aqua_tail34_r090_forced_template_rank1_task108_smoke_summary.jsonl",
            ),
        ]

        summary = build_forced_tail34_gate_summary(forced_runs=forced_runs)

        self.assertEqual(summary["rule"], "r092_bad_exact_gate_forced_tail34_validation")
        self.assertEqual(summary["num_tasks"], 5)
        self.assertEqual(summary["baseline_solved"], 3)
        self.assertEqual(summary["forced_template_solved"], 4)
        self.assertEqual(summary["gate_solved"], 4)
        self.assertEqual(summary["gate_fix_harm"], {"fix": 1, "harm": 0})
        self.assertEqual(sorted(summary["accepted_tasks"]), ["task_108", "task_188", "task_8"])
        self.assertEqual(sorted(summary["fallback_tasks"]), ["task_114", "task_56"])
        self.assertAlmostEqual(summary["total_forced_template_cost"], 0.20125, places=6)
        self.assertEqual(summary["decision_field_violations"], 0)


if __name__ == "__main__":
    unittest.main()
