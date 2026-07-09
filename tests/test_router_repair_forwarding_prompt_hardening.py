import unittest


class RouterRepairForwardingPromptHardeningTests(unittest.TestCase):
    def test_protocol_freezes_edge_prompt_repair_forwarding_before_api(self):
        from experiment.aqua.router_repair_forwarding_prompt_hardening import (
            build_evaluate_command,
            build_router_repair_forwarding_prompt_hardening,
        )

        command = build_evaluate_command()
        summary = build_router_repair_forwarding_prompt_hardening()

        self.assertEqual(
            summary["rule"], "r138_router_repair_forwarding_prompt_hardening"
        )
        self.assertTrue(summary["prompt_hardening_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["prompt_as_edge_first_class"])
        self.assertFalse(summary["node_only_promptnode_sufficient"])
        self.assertTrue(summary["r137_forwarding_gap_confirmed"])
        self.assertTrue(summary["pn_verifier_repair_status_values_hardened"])
        self.assertTrue(summary["pn_verifier_forbids_exact_as_repair_status"])
        self.assertTrue(summary["pn_router_repair_forwarding_required"])
        self.assertTrue(summary["router_supported_none_repair_coexistence"])
        self.assertTrue(summary["pn_router_does_not_reset_repair_fields"])
        self.assertEqual(
            summary["decision_method"], "EdgePromptRepairContractFinalRefer"
        )
        self.assertEqual(summary["switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["fallback_tasks"], ["task_8", "task_188"])
        self.assertIn("--decision_method EdgePromptRepairContractFinalRefer", command)
        self.assertIn(
            "aqua_tail34_r139_edge_prompt_repair_forwarding_switch_results.jsonl",
            command,
        )
        self.assertTrue(summary["same_two_switch_task_smoke_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])


if __name__ == "__main__":
    unittest.main()
