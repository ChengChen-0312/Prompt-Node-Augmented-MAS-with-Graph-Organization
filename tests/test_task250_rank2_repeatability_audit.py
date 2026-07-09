import unittest


class Task250Rank2RepeatabilityAuditTests(unittest.TestCase):
    def test_rank2_task250_repeated_runs_are_not_stable(self):
        from experiment.aqua.task250_rank2_repeatability_audit import build_repeatability_summary

        summary = build_repeatability_summary()

        self.assertEqual(summary["rule"], "r104_task250_rank2_repeatability_audit")
        self.assertEqual(summary["task_id"], "task_250")
        self.assertEqual(summary["rank"], 2)
        self.assertEqual(summary["num_repeats"], 2)
        self.assertEqual(summary["predictions"], ["E", "A"])
        self.assertEqual(summary["unique_predictions"], ["A", "E"])
        self.assertFalse(summary["stable_prediction"])
        self.assertEqual(summary["solved_pattern"], [True, False])
        self.assertEqual(
            summary["claim_boundary"],
            "task250 rank2 repeatability audit; no new API",
        )


if __name__ == "__main__":
    unittest.main()
