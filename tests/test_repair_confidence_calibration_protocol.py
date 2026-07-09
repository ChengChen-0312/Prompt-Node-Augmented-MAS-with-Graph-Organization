import unittest


class RepairConfidenceCalibrationProtocolTests(unittest.TestCase):
    def test_protocol_blocks_tail34_threshold_tuning_and_freezes_calibration_inputs(self):
        from experiment.aqua.repair_confidence_calibration_protocol import (
            build_repair_confidence_calibration_protocol,
        )

        summary = build_repair_confidence_calibration_protocol()

        self.assertEqual(summary["rule"], "r141_repair_confidence_calibration_protocol")
        self.assertTrue(summary["protocol_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["r140_alignment_confirmed"])
        self.assertTrue(summary["r139_forwarding_fixed"])
        self.assertTrue(summary["r139_low_confidence_rejection"])
        self.assertFalse(summary["direct_threshold_lowering_allowed"])
        self.assertFalse(summary["uses_tail34_training_source"])
        self.assertIn("tail34_true_answers_or_clean_labels", summary["forbidden_sources"])
        self.assertIn("tail34_task_ids", summary["forbidden_sources"])
        self.assertIn("r139_task250_confidence_as_threshold_target", summary["forbidden_sources"])
        self.assertIn("first200_non_tail34_option_binding_audit", summary["allowed_sources"])
        self.assertIn("synthetic_numeric_repair_controls", summary["allowed_sources"])
        self.assertIn("repair_distance_ratio", summary["calibration_features"])
        self.assertIn("direct_majority_contradiction", summary["calibration_features"])
        self.assertEqual(summary["required_clean_harm_guards"], ["task_8", "task_188"])
        self.assertEqual(summary["required_clean_recovery_targets"], ["task_250"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"], "repair_confidence_calibration_offline_export"
        )


if __name__ == "__main__":
    unittest.main()
