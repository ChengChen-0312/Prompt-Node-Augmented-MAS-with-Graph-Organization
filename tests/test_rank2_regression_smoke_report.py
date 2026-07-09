import unittest


class Rank2RegressionSmokeReportTests(unittest.TestCase):
    def test_rank2_smoke_rejects_r101_heuristic_as_deployable_selector(self):
        from experiment.aqua.rank2_regression_smoke_report import build_rank2_smoke_summary

        summary = build_rank2_smoke_summary()

        self.assertEqual(summary["rule"], "r103_rank2_regression_smoke_report")
        self.assertEqual(summary["num_tasks"], 4)
        self.assertEqual(summary["baseline_solved"], 2)
        self.assertEqual(summary["rank2_solved"], 2)
        self.assertEqual(summary["fix_harm"], "1/1")
        self.assertEqual(summary["clean_fix_harm"], "0/1")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["clean_harm_guard_harms"], ["task_188"])
        self.assertEqual(summary["clean_recovery_targets_solved"], [])
        self.assertEqual(summary["total_cost"], 0.1602)
        self.assertEqual(
            summary["claim_boundary"],
            "four-task rank2 regression smoke; rejects R101 heuristic as deployable selector",
        )


if __name__ == "__main__":
    unittest.main()
