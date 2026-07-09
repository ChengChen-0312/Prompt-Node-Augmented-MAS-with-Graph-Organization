import unittest


class Rank5RegressionSmokeProtocolTests(unittest.TestCase):
    def test_protocol_freezes_rank5_smoke_for_rank_consensus_check(self):
        from experiment.aqua.rank5_regression_smoke_protocol import build_protocol

        protocol = build_protocol()

        self.assertEqual(protocol["rule"], "r105_rank5_regression_smoke_protocol")
        self.assertEqual(protocol["selected_rank"], 5)
        self.assertEqual(protocol["comparison_rank"], 2)
        self.assertEqual(protocol["task_split_indices"], [8, 108, 188, 250])
        self.assertEqual(protocol["clean_harm_guard_tasks"], ["task_8", "task_188"])
        self.assertEqual(protocol["clean_recovery_targets"], ["task_250"])
        self.assertFalse(protocol["is_full_tail34"])
        self.assertEqual(
            protocol["claim_boundary"],
            "pre-registered four-task rank5 regression smoke for consensus check; no held-out accuracy claim",
        )


if __name__ == "__main__":
    unittest.main()
