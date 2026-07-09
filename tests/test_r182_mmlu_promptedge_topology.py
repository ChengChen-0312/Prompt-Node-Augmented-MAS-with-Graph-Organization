import unittest

import networkx as nx

from experiment.mmlu.promptedge_topology import (
    inject_promptedge_topology,
    promptedge_topology_to_pyg,
)
from mas_framework.agents.prompt_node import (
    PromptNode,
    _extract_multiple_choice_options,
)
from mas_framework.graph.graph import TestGraph


class TestR182MMLUPromptEdgeTopology(unittest.TestCase):
    def test_promptnode_extracts_mmlu_option_prefixes_and_contract_labels(self):
        task = (
            "What is conserved in an elastic collision?\n"
            "Option A: momentum only\n"
            "Option B: kinetic energy only\n"
            "Option C: momentum and kinetic energy\n"
            "Option D: neither"
        )

        options = _extract_multiple_choice_options(task)
        self.assertEqual(set(options), {"A", "B", "C", "D"})

        router_contract = PromptNode(role="PN_Router", llm_name="mock")._role_contract(options)
        self.assertIn("SUPPORTED_OPTION: A/B/C/D/NONE", router_contract)
        self.assertIn("REPAIR_OPTION: A/B/C/D/NONE", router_contract)
        self.assertNotIn("SUPPORTED_OPTION: A/B/C/D/E/NONE", router_contract)

    def test_inject_promptedge_topology_produces_dag_with_edge_permissions(self):
        graph = nx.DiGraph()
        graph.add_node(0, role="Knowlegable Expert", constraint="expert")
        graph.add_node(1, role="Critic", constraint="critic")
        graph.add_edge(0, 1)

        augmented = inject_promptedge_topology(graph)

        roles = nx.get_node_attributes(augmented, "role")
        self.assertEqual(roles[2], "PN_Memory")
        self.assertEqual(roles[3], "PN_Verifier")
        self.assertEqual(roles[4], "PN_Router")
        self.assertTrue(nx.is_directed_acyclic_graph(augmented))
        self.assertEqual(augmented.graph["decision_exposure_policy"], "terminal")

        edge_meta = nx.get_edge_attributes(augmented, "promptedge_permission")
        self.assertEqual(edge_meta[(0, 2)], "read")
        self.assertEqual(edge_meta[(1, 2)], "read")
        self.assertEqual(edge_meta[(2, 3)], "write")
        self.assertEqual(edge_meta[(3, 4)], "forward")

    def test_promptedge_topology_to_pyg_constructs_mmlu_testgraph(self):
        graph = nx.DiGraph()
        graph.add_node(0, role="Knowlegable Expert", constraint="expert")
        graph.add_node(1, role="Critic", constraint="critic")
        graph.add_edge(0, 1)

        augmented = inject_promptedge_topology(graph)
        pyg = promptedge_topology_to_pyg(
            augmented,
            task_text=(
                "What is 2+2?\n"
                "Option A: 1\n"
                "Option B: 2\n"
                "Option C: 3\n"
                "Option D: 4"
            ),
        )
        constructed = TestGraph(
            domain="mmlu",
            llm_name="gpt-4o-2024-08-06",
            decision_method="FinalRefer",
            pyg_data=pyg,
        )

        self.assertEqual(getattr(pyg, "decision_exposure_policy"), "terminal")
        self.assertEqual(len(getattr(pyg, "promptedge_meta")), augmented.number_of_edges())
        self.assertEqual(
            [getattr(node, "role", "") for node in constructed.nodes.values()],
            ["Knowlegable Expert", "Critic", "PN_Memory", "PN_Verifier", "PN_Router"],
        )


if __name__ == "__main__":
    unittest.main()
