import subprocess
import sys
import unittest

import networkx as nx


class GraphPolicyGenerationAuditTests(unittest.TestCase):
    def test_summarize_generated_graphs_counts_promptnode_roles_and_dags(self):
        from experiment.aqua.graph_policy_generation_audit import summarize_generated_graphs

        g1 = nx.DiGraph()
        g1.add_node(0, role="Math Solver")
        g1.add_node(1, role="PN_Verifier")
        g1.add_edge(0, 1)

        g2 = nx.DiGraph()
        g2.add_node(0, role="Inspector")
        g2.add_node(1, role="PN_Memory")
        g2.add_node(2, role="PN_Router")
        g2.add_edges_from([(0, 1), (1, 2)])

        g3 = nx.DiGraph()
        g3.add_node(0, role="Inspector")
        g3.add_node(1, role="Math Solver")
        g3.add_edges_from([(0, 1), (1, 0)])

        summary = summarize_generated_graphs([g1, g2, g3])

        self.assertEqual(summary["sampled_graphs"], 3)
        self.assertEqual(summary["promptnode_graphs"], 2)
        self.assertEqual(summary["promptnode_nodes"], 3)
        self.assertEqual(summary["dag_graphs"], 2)
        self.assertEqual(summary["role_counts"]["PN_Verifier"], 1)
        self.assertEqual(summary["role_counts"]["PN_Memory"], 1)
        self.assertEqual(summary["role_counts"]["PN_Router"], 1)

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/graph_policy_generation_audit.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
