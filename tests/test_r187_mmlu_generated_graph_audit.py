import unittest

import networkx as nx

from experiment.mmlu.r187_promptedge_generated_graph_audit import audit_generated_graph


class TestR187MMLUGeneratedGraphAudit(unittest.TestCase):
    def test_audit_detects_promptnode_chain_and_terminal_router(self):
        graph = nx.DiGraph()
        graph.add_node(0, role="Knowlegable Expert")
        graph.add_node(1, role="PN_Memory")
        graph.add_node(2, role="PN_Verifier")
        graph.add_node(3, role="PN_Router")
        graph.add_edges_from([(0, 1), (1, 2), (2, 3)])

        audit = audit_generated_graph(graph)

        self.assertTrue(audit["is_dag"])
        self.assertTrue(audit["has_any_pn"])
        self.assertTrue(audit["has_all_pn_roles"])
        self.assertTrue(audit["has_pn_chain"])
        self.assertTrue(audit["router_is_terminal"])

    def test_audit_rejects_router_without_chain(self):
        graph = nx.DiGraph()
        graph.add_node(0, role="PN_Router")
        graph.add_node(1, role="Critic")
        graph.add_edge(0, 1)

        audit = audit_generated_graph(graph)

        self.assertTrue(audit["has_any_pn"])
        self.assertFalse(audit["has_all_pn_roles"])
        self.assertFalse(audit["has_pn_chain"])
        self.assertFalse(audit["router_is_terminal"])


if __name__ == "__main__":
    unittest.main()
