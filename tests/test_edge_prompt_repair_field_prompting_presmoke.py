import unittest


class EdgePromptRepairFieldPromptingPresmokeTests(unittest.TestCase):
    def test_presmoke_freezes_repair_prompting_and_bounded_api_command(self):
        from experiment.aqua.edge_prompt_repair_field_prompting_presmoke import (
            REPAIR_FIELD_NAMES,
            build_edge_prompt_repair_field_prompting_presmoke,
            build_evaluate_command,
            write_switch_task_split,
        )

        payload = write_switch_task_split()
        command = build_evaluate_command()
        summary = build_edge_prompt_repair_field_prompting_presmoke()

        self.assertEqual(payload["test_indices"], [108, 250])
        self.assertIn("--decision_method EdgePromptRepairContractFinalRefer", command)
        self.assertIn("--forced_template_candidate_rank 5", command)
        self.assertEqual(summary["rule"], "r136_edge_prompt_repair_field_prompting_presmoke")
        self.assertTrue(summary["presmoke_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["pn_verifier_repair_audit_prompted"])
        self.assertTrue(summary["pn_router_repair_fields_prompted"])
        self.assertEqual(summary["repair_field_names"], REPAIR_FIELD_NAMES)
        self.assertTrue(summary["r134_repair_gate_ready"])
        self.assertEqual(summary["decision_method"], "EdgePromptRepairContractFinalRefer")
        self.assertEqual(summary["switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["fallback_tasks"], ["task_8", "task_188"])
        self.assertTrue(summary["same_four_task_smoke_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])


if __name__ == "__main__":
    unittest.main()
