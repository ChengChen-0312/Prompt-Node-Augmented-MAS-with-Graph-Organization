import os
import sys
import unittest
from unittest import mock

import networkx as nx


class PromptNodeFinetuneHookTests(unittest.TestCase):
    def test_prepare_efficient_graph_for_execution_applies_prompt_nodes_before_pyg(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.finetune_aqua import prepare_efficient_graph_for_execution

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver", constraint="solve")
        graph.add_node(1, role="Inspector", constraint="inspect")
        graph.add_edge(0, 1, label=1)

        augmented_graph, pyg_graph = prepare_efficient_graph_for_execution(
            graph, "AQuA task", prompt_node_policy="memory_verifier"
        )

        roles = [node_data["role"] for node_data in pyg_graph.x]
        self.assertIn("PN_Memory", roles)
        self.assertIn("PN_Verifier", roles)
        self.assertNotIn("PN_Router", roles)
        self.assertEqual(augmented_graph.graph["prompt_node_policy"], "memory_verifier")
        self.assertEqual(pyg_graph.prompt_node_policy, "memory_verifier")
        self.assertEqual(pyg_graph.num_nodes, 4)

    def test_prepare_efficient_graph_for_execution_canonicalizes_generated_prompt_nodes(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.finetune_aqua import prepare_efficient_graph_for_execution

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver", constraint="solve")
        graph.add_node(1, role="Programming Expert", constraint="code")
        graph.add_node(2, role="PN_Router", constraint="route")
        graph.add_node(3, role="PN_Router", constraint="route")
        graph.add_edge(0, 1, label=1)
        graph.add_edge(0, 3, label=1)
        graph.add_edge(1, 2, label=1)

        normalized_graph, pyg_graph = prepare_efficient_graph_for_execution(
            graph,
            "AQuA task",
            prompt_node_policy="none",
            prompt_node_topology_policy="canonicalize_generated",
        )

        roles = [node_data["role"] for node_data in pyg_graph.x]
        self.assertEqual(roles.count("PN_Memory"), 1)
        self.assertEqual(roles.count("PN_Verifier"), 1)
        self.assertEqual(roles.count("PN_Router"), 1)
        self.assertTrue(normalized_graph.graph["canonicalized_prompt_nodes"])
        self.assertEqual(pyg_graph.prompt_node_topology_policy, "canonicalize_generated")

    def test_cli_accepts_custom_finetune_data_dir(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.finetune_aqua import parse_cli_args

        with mock.patch.object(
            sys,
            "argv",
            ["finetune_aqua.py", "--finetune_data_dir", "../FinetuneData_AQuA_PN_clean"],
        ):
            args = parse_cli_args()

        self.assertEqual(args.finetune_data_dir, "../FinetuneData_AQuA_PN_clean")

    def test_cli_accepts_prompt_node_topology_policy(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.finetune_aqua import parse_cli_args

        with mock.patch.object(
            sys,
            "argv",
            [
                "finetune_aqua.py",
                "--prompt_node_topology_policy",
                "canonicalize_generated",
            ],
        ):
            args = parse_cli_args()

        self.assertEqual(args.prompt_node_topology_policy, "canonicalize_generated")


if __name__ == "__main__":
    unittest.main()
