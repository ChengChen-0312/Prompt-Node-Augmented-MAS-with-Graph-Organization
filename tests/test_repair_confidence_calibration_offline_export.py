import unittest


class RepairConfidenceCalibrationOfflineExportTests(unittest.TestCase):
    def test_export_uses_synthetic_controls_and_marks_r139_eval_only(self):
        from experiment.aqua.repair_confidence_calibration_offline_export import (
            build_repair_confidence_calibration_offline_export,
        )

        summary = build_repair_confidence_calibration_offline_export()

        self.assertEqual(summary["rule"], "r142_repair_confidence_calibration_offline_export")
        self.assertTrue(summary["offline_export_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertFalse(summary["uses_tail34_training_source"])
        self.assertFalse(summary["direct_threshold_lowering_allowed"])
        self.assertGreaterEqual(summary["synthetic_control_rows"], 6)
        self.assertEqual(summary["forbidden_training_field_violations"], 0)
        self.assertEqual(summary["accepted_positive_controls"], 3)
        self.assertEqual(summary["rejected_negative_controls"], 3)
        self.assertTrue(summary["r139_task250_eval_only"])
        self.assertFalse(summary["r139_task250_used_for_training"])
        self.assertGreaterEqual(summary["r139_task250_calibrated_confidence"], 0.8)
        self.assertTrue(summary["r139_task250_calibration_would_pass"])
        self.assertEqual(summary["required_clean_harm_guards"], ["task_8", "task_188"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "calibrated_repair_final_gate_offline_replay",
        )


if __name__ == "__main__":
    unittest.main()
