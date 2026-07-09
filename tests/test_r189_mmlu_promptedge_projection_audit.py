import unittest

import networkx as nx

from experiment.mmlu.r189_promptedge_projection_audit import (
    project_generated_graph_to_promptedge_contract,
    strip_promptnodes,
)
from experiment.mmlu.r187_promptedge_generated_graph_audit import audit_generated_graph


class TestR189MMLUPromptEdgeProjectionAudit(unittest.TestCase):
    def test_strip_promptnodes_preserves_non_pn_agent_edges(self):
        graph = nx.DiGraph()
        graph.add_node(0, role="Knowlegable Expert")
        graph.add_node(1, role="Critic")
        graph.add_node(2, role="PN_Router")
        graph.add_edges_from([(0, 1), (1, 2)])

        stripped = strip_promptnodes(graph)

        self.assertEqual([data["role"] for _, data in stripped.nodes(data=True)], ["Knowlegable Expert", "Critic"])
        self.assertTrue(stripped.has_edge(0, 1))

    def test_projection_turns_partial_pn_graph_into_contract_ready_topology(self):
        graph = nx.DiGraph()
        graph.add_node(0, role="Knowlegable Expert")
        graph.add_node(1, role="PN_Router")
        graph.add_node(2, role="Critic")
        graph.add_edges_from([(0, 1), (0, 2)])

        projected = project_generated_graph_to_promptedge_contract(graph)
        audit = audit_generated_graph(projected)

        self.assertTrue(audit["is_dag"])
        self.assertTrue(audit["has_all_pn_roles"])
        self.assertTrue(audit["has_pn_chain"])
        self.assertTrue(audit["router_is_terminal"])
        self.assertTrue(audit["promptedge_contract_ready"])


if __name__ == "__main__":
    unittest.main()
