import unittest


class ObjectiveSafetyRank5GuardReplayTests(unittest.TestCase):
    def test_guard_keeps_rank5_clean_recovery_without_regression_harms(self):
        from experiment.aqua.objective_safety_rank5_guard_replay import build_guard_summary

        summary = build_guard_summary()

        self.assertEqual(summary["rule"], "r107_objective_safety_rank5_guard_replay")
        self.assertEqual(summary["num_tasks"], 4)
        self.assertEqual(summary["baseline_solved"], 2)
        self.assertEqual(summary["rank5_solved"], 3)
        self.assertEqual(summary["guarded_solved"], 4)
        self.assertEqual(summary["switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["fallback_tasks"], ["task_8", "task_188"])
        self.assertEqual(summary["fix_harm"], "2/0")
        self.assertEqual(summary["clean_fix_harm"], "1/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["suppressed_rank5_harm_tasks"], ["task_8"])
        self.assertEqual(summary["selector_input_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "four-task replay over R106 rank5 outputs and R095 objective-safety features",
        )


if __name__ == "__main__":
    unittest.main()
