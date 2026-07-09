import unittest


class EdgePromptRepairSmokeReportTests(unittest.TestCase):
    def test_report_tracks_repair_field_presence_and_forwarding_gap(self):
        from experiment.aqua.edge_prompt_repair_smoke_report import (
            build_edge_prompt_repair_smoke_summary,
        )

        summary = build_edge_prompt_repair_smoke_summary()

        self.assertEqual(summary["rule"], "r137_edge_prompt_repair_smoke")
        self.assertEqual(summary["decision_method"], "EdgePromptRepairContractFinalRefer")
        self.assertEqual(summary["baseline_accuracy"], "2/4")
        self.assertEqual(summary["selected_accuracy"], "3/4")
        self.assertEqual(summary["clean_fix_harm"], "0/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["switch_router_repair_fields_present"], "2/2")
        self.assertEqual(summary["switch_router_repair_option_non_none"], "0/2")
        self.assertTrue(summary["task250_verifier_repair_candidate_present"])
        self.assertFalse(summary["task250_router_repair_forwarded"])
        self.assertTrue(summary["verifier_router_repair_forwarding_gap"])
        self.assertTrue(summary["integrity_gate_passed"])
        self.assertFalse(summary["smoke_gate_passed"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_protocol"], "router_repair_field_forwarding_prompt_hardening")


if __name__ == "__main__":
    unittest.main()
