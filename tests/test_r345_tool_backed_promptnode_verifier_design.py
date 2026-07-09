import unittest


class TestR345ToolBackedPromptnodeVerifierDesign(unittest.TestCase):
    def test_design_replaces_prompt_only_verifiers_with_general_executable_promptnodes(self):
        from experiment.mmlu.r345_tool_backed_promptnode_verifier_design import build_tool_backed_design

        summary = build_tool_backed_design()
        node_ids = {node["id"] for node in summary["tool_backed_promptnodes"]}

        self.assertEqual(summary["run_id"], "R345")
        self.assertIn("PN_CoordinateTransformer", node_ids)
        self.assertIn("PN_FiniteAbelianGroupEnumerator", node_ids)
        self.assertIn("PN_FiniteFieldDerivativeAnalyzer", node_ids)
        self.assertIn("PN_RedoxBalanceLinearSolver", node_ids)
        self.assertTrue(all(node["executor_type"] == "deterministic_local_tool" for node in summary["tool_backed_promptnodes"]))
        self.assertFalse(summary["uses_true_answers"])
        self.assertFalse(summary["uses_task_ids_or_known_wrong_items"])
        self.assertIn("reject_if_unparsed_or_inconsistent", summary["promptedge_contracts"])
        self.assertTrue(summary["local_preflight_authorized_next"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R346_tool_backed_promptnode_local_preflight")


if __name__ == "__main__":
    unittest.main()
