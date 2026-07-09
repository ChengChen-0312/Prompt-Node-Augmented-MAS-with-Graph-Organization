import unittest


class Task250TemplateRankSweepReportTests(unittest.TestCase):
    def test_rank_sweep_finds_two_clean_task250_matching_templates(self):
        from experiment.aqua.task250_template_rank_sweep_report import build_rank_sweep_summary

        summary = build_rank_sweep_summary()

        self.assertEqual(summary["rule"], "r100_task250_template_rank_sweep_report")
        self.assertEqual(summary["task_id"], "task_250")
        self.assertEqual(summary["desired_prediction"], "E")
        self.assertEqual(summary["sweep_ranks"], [2, 3, 4, 5])
        self.assertEqual(summary["matching_ranks"], [2, 5])
        self.assertEqual(summary["nonmatching_ranks"], [3, 4])
        self.assertEqual(summary["best_matching_rank"], 2)
        self.assertEqual(summary["num_matching_ranks"], 2)
        self.assertAlmostEqual(summary["total_cost"], 0.14663, places=6)
        self.assertEqual(
            summary["claim_boundary"],
            "one-task task250 rank sweep; not held-out accuracy",
        )


if __name__ == "__main__":
    unittest.main()
