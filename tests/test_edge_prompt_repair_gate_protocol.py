import unittest


class EdgePromptRepairGateProtocolTests(unittest.TestCase):
    def test_protocol_reports_gate_accept_reject_and_r132_boundary(self):
        from experiment.aqua.edge_prompt_repair_gate_protocol import (
            build_edge_prompt_repair_gate_protocol,
        )

        summary = build_edge_prompt_repair_gate_protocol()

        self.assertEqual(summary["rule"], "r134_edge_prompt_repair_gate_protocol")
        self.assertTrue(summary["implementation_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertEqual(summary["decision_method"], "EdgePromptRepairContractFinalRefer")
        self.assertTrue(summary["decision_method_registered"])
        self.assertEqual(summary["explicit_repair_prediction"], "The answer is E")
        self.assertEqual(summary["explicit_repair_parser_prediction"], "E")
        self.assertEqual(summary["missing_repair_parser_prediction"], "None.")
        self.assertTrue(summary["low_confidence_rejected"])
        self.assertTrue(summary["large_distance_rejected"])
        self.assertFalse(summary["r132_task250_has_repair_fields"])
        self.assertEqual(summary["r132_task250_repair_gate_parser_prediction"], "None.")
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_protocol"], "edge_prompt_repair_field_prompting_presmoke")


if __name__ == "__main__":
    unittest.main()
