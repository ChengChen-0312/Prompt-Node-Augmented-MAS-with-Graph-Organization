import unittest


class Rank5RegressionSmokeReportTests(unittest.TestCase):
    def test_rank5_smoke_recovers_task250_but_is_not_clean_safe_or_consensus_ready(self):
        from experiment.aqua.rank5_regression_smoke_report import build_rank5_smoke_summary

        summary = build_rank5_smoke_summary()

        self.assertEqual(summary["rule"], "r106_rank5_regression_smoke_report")
        self.assertEqual(summary["num_tasks"], 4)
        self.assertEqual(summary["baseline_solved"], 2)
        self.assertEqual(summary["rank5_solved"], 3)
        self.assertEqual(summary["fix_harm"], "2/1")
        self.assertEqual(summary["clean_fix_harm"], "1/1")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["clean_harm_guard_harms"], ["task_8"])
        self.assertEqual(summary["clean_recovery_targets_solved"], ["task_250"])
        self.assertEqual(summary["rank2_rank5_consensus_tasks"], ["task_108"])
        self.assertEqual(summary["consensus_clean_recovery_solved"], [])
        self.assertEqual(
            summary["claim_boundary"],
            "four-task rank5 regression smoke; consensus not clean-safe",
        )


if __name__ == "__main__":
    unittest.main()
