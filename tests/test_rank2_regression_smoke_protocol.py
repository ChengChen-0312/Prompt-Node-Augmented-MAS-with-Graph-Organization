import unittest


class Rank2RegressionSmokeProtocolTests(unittest.TestCase):
    def test_protocol_freezes_rank2_regression_smoke_before_api(self):
        from experiment.aqua.rank2_regression_smoke_protocol import build_protocol

        protocol = build_protocol()

        self.assertEqual(protocol["rule"], "r102_rank2_regression_smoke_protocol")
        self.assertEqual(protocol["selected_rank"], 2)
        self.assertEqual(protocol["task_split_indices"], [8, 108, 188, 250])
        self.assertEqual(protocol["clean_harm_guard_tasks"], ["task_8", "task_188"])
        self.assertEqual(protocol["clean_recovery_targets"], ["task_250"])
        self.assertEqual(protocol["noisy_optional_targets"], ["task_108"])
        self.assertFalse(protocol["is_full_tail34"])
        self.assertEqual(
            protocol["claim_boundary"],
            "pre-registered four-task rank2 regression smoke; no held-out accuracy claim",
        )


if __name__ == "__main__":
    unittest.main()
