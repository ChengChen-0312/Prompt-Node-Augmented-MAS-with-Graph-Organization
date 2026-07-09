import unittest


class CalibratedRepairApiSmokeReportTests(unittest.TestCase):
    def test_report_tracks_calibrated_clean_repair_without_broad_api(self):
        from experiment.aqua.calibrated_repair_api_smoke_report import (
            build_calibrated_repair_api_smoke_summary,
        )

        summary = build_calibrated_repair_api_smoke_summary()

        self.assertEqual(summary["rule"], "r146_bounded_calibrated_repair_api_smoke")
        self.assertEqual(summary["decision_method"], "CalibratedEdgePromptRepairContractFinalRefer")
        self.assertEqual(summary["baseline_accuracy"], "2/4")
        self.assertEqual(summary["selected_accuracy"], "4/4")
        self.assertEqual(summary["fix_harm"], "2/0")
        self.assertEqual(summary["clean_fix_harm"], "1/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["switch_router_repair_fields_present"], "2/2")
        self.assertEqual(summary["switch_router_repair_option_non_none"], "1/2")
        self.assertTrue(summary["task250_verifier_repair_candidate_present"])
        self.assertTrue(summary["task250_router_repair_forwarded"])
        self.assertFalse(summary["verifier_router_repair_forwarding_gap"])
        self.assertEqual(summary["task250_router_repair_option"], "E")
        self.assertEqual(summary["task250_router_repair_confidence"], 0.75)
        self.assertEqual(summary["task250_calibrated_repair_confidence"], 0.85)
        self.assertTrue(summary["task250_calibrated_repair_gate_passed"])
        self.assertTrue(summary["integrity_gate_passed"])
        self.assertTrue(summary["smoke_gate_passed"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "r147_bounded_smoke_result_to_claim_and_expansion_protocol",
        )


if __name__ == "__main__":
    unittest.main()
