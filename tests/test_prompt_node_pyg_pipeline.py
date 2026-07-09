import os
import sys
import unittest
from unittest import mock

import networkx as nx


class PromptNodePygPipelineTests(unittest.TestCase):
    def test_evaluate_policy_helper_augments_graph_before_pyg_conversion(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.evaluate_aqua import apply_prompt_node_policy_to_graph
        from experiment.aqua.prompt_node_graph import is_prompt_node_role
        from experiment.utils import convert_to_pyg_graph

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver", constraint="solve")
        graph.add_node(1, role="Inspector", constraint="inspect")
        graph.add_edge(0, 1, label=1)

        augmented = apply_prompt_node_policy_to_graph(
            graph, prompt_node_policy="memory_verifier_router"
        )
        pyg_graph = convert_to_pyg_graph(augmented, "AQuA task")

        roles = [node_data["role"] for node_data in pyg_graph.x]
        self.assertIn("PN_Memory", roles)
        self.assertIn("PN_Verifier", roles)
        self.assertIn("PN_Router", roles)
        self.assertTrue(any(is_prompt_node_role(role) for role in roles))
        self.assertEqual(pyg_graph.num_nodes, 5)
        self.assertGreaterEqual(pyg_graph.edge_index.shape[1], 5)

    def test_evaluate_policy_helper_canonicalizes_generated_prompt_nodes(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.evaluate_aqua import apply_prompt_node_policy_to_graph
        from experiment.utils import convert_to_pyg_graph

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver", constraint="solve")
        graph.add_node(1, role="Programming Expert", constraint="code")
        graph.add_node(2, role="PN_Router", constraint="route")
        graph.add_node(3, role="PN_Router", constraint="route")
        graph.add_edge(0, 1, label=1)
        graph.add_edge(0, 3, label=1)
        graph.add_edge(1, 2, label=1)

        normalized = apply_prompt_node_policy_to_graph(
            graph,
            prompt_node_policy="none",
            prompt_node_topology_policy="canonicalize_generated",
        )
        pyg_graph = convert_to_pyg_graph(normalized, "AQuA task")

        roles = [node_data["role"] for node_data in pyg_graph.x]
        self.assertEqual(roles.count("PN_Memory"), 1)
        self.assertEqual(roles.count("PN_Verifier"), 1)
        self.assertEqual(roles.count("PN_Router"), 1)
        self.assertEqual(pyg_graph.num_nodes, 5)

    def test_decision_exposure_policy_can_be_overridden_for_selective_gate(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.evaluate_aqua import (
            parse_args,
            resolve_decision_exposure_policy,
        )

        graph = nx.DiGraph()
        graph.graph["canonicalized_prompt_nodes"] = True

        self.assertEqual(resolve_decision_exposure_policy(graph, "auto"), "terminal")
        self.assertEqual(resolve_decision_exposure_policy(graph, "all"), "all")
        self.assertEqual(resolve_decision_exposure_policy(nx.DiGraph(), "terminal"), "terminal")

        with mock.patch.object(
            sys,
            "argv",
            ["evaluate_aqua.py", "--decision_exposure_policy", "all"],
        ):
            args = parse_args()
        self.assertEqual(args.decision_exposure_policy, "all")


if __name__ == "__main__":
    unittest.main()
