import unittest


class EdgePromptRepairForwardingSmokeReportTests(unittest.TestCase):
    def test_report_tracks_forwarded_repair_and_low_confidence_rejection(self):
        from experiment.aqua.edge_prompt_repair_forwarding_smoke_report import (
            build_edge_prompt_repair_forwarding_smoke_summary,
        )

        summary = build_edge_prompt_repair_forwarding_smoke_summary()

        self.assertEqual(summary["rule"], "r139_edge_prompt_repair_forwarding_smoke")
        self.assertEqual(summary["baseline_accuracy"], "2/4")
        self.assertEqual(summary["selected_accuracy"], "3/4")
        self.assertEqual(summary["clean_fix_harm"], "0/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["switch_router_repair_fields_present"], "2/2")
        self.assertEqual(summary["switch_router_repair_option_non_none"], "1/2")
        self.assertTrue(summary["task250_verifier_repair_candidate_present"])
        self.assertTrue(summary["task250_router_repair_forwarded"])
        self.assertFalse(summary["verifier_router_repair_forwarding_gap"])
        self.assertEqual(summary["task250_router_repair_option"], "E")
        self.assertEqual(
            summary["task250_router_repair_binding_status"],
            "NUMERIC_NEAREST_WITH_TYPO_CHECK",
        )
        self.assertEqual(summary["task250_router_repair_confidence"], 0.5)
        self.assertEqual(summary["repair_min_confidence"], 0.8)
        self.assertFalse(summary["task250_repair_confidence_gate_passed"])
        self.assertTrue(summary["task250_repair_forwarded_but_rejected_low_confidence"])
        self.assertTrue(summary["integrity_gate_passed"])
        self.assertFalse(summary["smoke_gate_passed"])
        self.assertFalse(summary["broad_api_allowed_next"])


if __name__ == "__main__":
    unittest.main()
