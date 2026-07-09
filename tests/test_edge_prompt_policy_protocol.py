import unittest


class EdgePromptPolicyProtocolTests(unittest.TestCase):
    def test_protocol_materializes_prompt_as_edge_schema_and_blocks_tail34_training(self):
        from experiment.aqua.edge_prompt_policy_protocol import (
            REQUIRED_EDGE_PROMPT_FIELDS,
            build_edge_prompt_policy_protocol,
        )

        rows, summary = build_edge_prompt_policy_protocol()

        self.assertEqual(summary["rule"], "r133_edge_prompt_policy_protocol")
        self.assertTrue(summary["protocol_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["prompt_as_edge_first_class"])
        self.assertFalse(summary["node_only_promptnode_sufficient"])
        self.assertFalse(summary["uses_tail34_training_source"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertTrue(summary["multi_dataset_transfer_required"])
        self.assertTrue(summary["no_task_id_routing"])
        self.assertIn("tail34_true_answers_or_clean_labels", summary["forbidden_training_sources"])
        self.assertIn("tail34_r132_switch_outputs", summary["forbidden_training_sources"])
        self.assertEqual(set(summary["edge_prompt_schema_fields"]), REQUIRED_EDGE_PROMPT_FIELDS)
        self.assertIn("evidence_write", summary["edge_prompt_types"])
        self.assertIn("memory_to_verifier_read", summary["edge_prompt_types"])
        self.assertIn("verifier_to_router_forward", summary["edge_prompt_types"])
        self.assertIn("router_to_final_answer_contract", summary["edge_prompt_types"])
        self.assertIn("mismatch_repair_escalation", summary["edge_prompt_types"])
        self.assertGreaterEqual(len(rows), 4)

    def test_selected_switch_templates_receive_edge_prompt_specs(self):
        from experiment.aqua.edge_prompt_policy_protocol import (
            REQUIRED_EDGE_PROMPT_FIELDS,
            build_edge_prompt_policy_protocol,
        )

        rows, summary = build_edge_prompt_policy_protocol()
        switch_rows = [row for row in rows if row["planned_action"] == "switch_to_promptnode_template"]

        self.assertEqual(summary["switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["switches_with_edge_prompt_specs"], "2/2")
        self.assertEqual(summary["switches_with_repair_edge_prompt"], "2/2")
        for row in switch_rows:
            self.assertGreaterEqual(row["edge_prompt_count"], 6)
            self.assertFalse(row["edge_prompt_selector_input_violation"])
            for spec in row["edge_prompt_specs"]:
                self.assertTrue(REQUIRED_EDGE_PROMPT_FIELDS.issubset(spec.keys()))
                self.assertNotIn("task_id", spec)
                self.assertNotIn("true_answer", spec)
                self.assertNotIn("question", spec)
                self.assertIn("no_nearest_choice_without_repair_contract", spec["option_binding_policy"])
                self.assertIn("transfer_required", spec["robustness_scope"])

    def test_r132_clean_gate_failure_redirects_to_edge_prompt_repair_not_broad_api(self):
        from experiment.aqua.edge_prompt_policy_protocol import build_edge_prompt_policy_protocol

        _, summary = build_edge_prompt_policy_protocol()

        self.assertEqual(summary["r132_smoke_gate_passed"], False)
        self.assertEqual(summary["r132_exact_option_repair_required"], True)
        self.assertEqual(summary["next_protocol"], "edge_prompt_exact_option_repair_protocol_before_api")
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertIn("task_250", summary["required_clean_recovery_targets"])


if __name__ == "__main__":
    unittest.main()
