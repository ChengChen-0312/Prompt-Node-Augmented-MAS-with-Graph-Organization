import unittest

import networkx as nx

from experiment.mmlu.promptedge_topology import (
    inject_promptedge_topology,
    promptedge_topology_to_pyg,
)
from experiment.mmlu.r191_projected_promptedge_smoke import (
    build_promptedge_logging_payload,
)


class TestR213MMLUProjectedSmokeLogging(unittest.TestCase):
    def test_logging_payload_contains_raw_projected_edges_and_router_schema(self):
        raw = nx.DiGraph()
        raw.add_node(0, role="Knowlegable Expert")
        raw.add_node(1, role="Critic")
        raw.add_edge(0, 1)
        projected = inject_promptedge_topology(raw, decision_exposure_policy="all")
        task_text = (
            "What is conserved?\n"
            "Option A: momentum\n"
            "Option B: energy\n"
            "Option C: mass\n"
            "Option D: charge"
        )
        pyg = promptedge_topology_to_pyg(projected, task_text)

        payload = build_promptedge_logging_payload(raw, projected, pyg, task_text)

        self.assertEqual(payload["raw_graph"]["roles"], ["Knowlegable Expert", "Critic"])
        self.assertEqual(payload["raw_graph"]["edges"], [[0, 1]])
        self.assertEqual(
            payload["projected_graph"]["roles"][-3:],
            ["PN_Memory", "PN_Verifier", "PN_Router"],
        )
        self.assertIn("read", payload["promptedge_permissions"])
        self.assertIn("write", payload["promptedge_permissions"])
        self.assertIn("forward", payload["promptedge_permissions"])
        self.assertTrue(payload["promptedge_text_as_edge_prompt"])
        self.assertEqual(
            payload["router_final_schema"]["allowed_option_labels"],
            ["A", "B", "C", "D", "NONE"],
        )
        self.assertTrue(payload["router_final_abstain_only"])


if __name__ == "__main__":
    unittest.main()
