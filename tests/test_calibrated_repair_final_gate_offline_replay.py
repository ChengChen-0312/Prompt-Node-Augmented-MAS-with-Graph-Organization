import unittest


class CalibratedRepairFinalGateOfflineReplayTests(unittest.TestCase):
    def test_replay_recovers_task250_without_clean_harm_before_api(self):
        from experiment.aqua.calibrated_repair_final_gate_offline_replay import (
            build_calibrated_repair_final_gate_offline_replay,
        )

        summary = build_calibrated_repair_final_gate_offline_replay()

        self.assertEqual(summary["rule"], "r143_calibrated_repair_final_gate_offline_replay")
        self.assertTrue(summary["offline_replay_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertEqual(summary["baseline_accuracy"], "2/4")
        self.assertEqual(summary["r139_selected_accuracy"], "3/4")
        self.assertEqual(summary["calibrated_selected_accuracy"], "4/4")
        self.assertEqual(summary["clean_fix_harm"], "1/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["task250_calibrated_prediction"], "E")
        self.assertGreaterEqual(summary["task250_calibrated_confidence"], 0.8)
        self.assertTrue(summary["clean_harm_guard_passed"])
        self.assertFalse(summary["uses_tail34_training_source"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "calibrated_repair_final_gate_implementation_presmoke",
        )


if __name__ == "__main__":
    unittest.main()
