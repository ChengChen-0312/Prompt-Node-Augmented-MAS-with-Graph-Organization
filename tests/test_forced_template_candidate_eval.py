import subprocess
import sys
import unittest


class ForcedTemplateCandidateEvalTests(unittest.TestCase):
    def test_candidate_record_reconstructs_promptnode_networkx_graph(self):
        from experiment.aqua.tail34_template_candidate_materialize import (
            build_tail34_candidates_from_files,
            candidate_record_to_networkx,
        )

        rows, _ = build_tail34_candidates_from_files(top_k=1)
        graph = candidate_record_to_networkx(rows[0]["candidates"][0])

        roles = [graph.nodes[node]["role"] for node in graph.nodes]
        self.assertEqual(roles[-3:], ["PN_Memory", "PN_Verifier", "PN_Router"])
        self.assertTrue(graph.graph["forced_template_candidate"])
        self.assertEqual(graph.graph["decision_exposure_policy"], "terminal")
        self.assertEqual(graph.graph["prompt_node_topology_policy"], "clean_fix_template")
        self.assertEqual(graph.nodes[2]["identity_type"], "Memory")
        self.assertEqual(graph.nodes[3]["identity_type"], "Instruction/Verifier")
        self.assertEqual(graph.edges[3, 4]["permissions"], ["read", "forward"])

    def test_evaluator_loads_and_selects_forced_template_graph_by_rank(self):
        from experiment.aqua.evaluate_aqua import (
            load_forced_template_candidate_pool,
            select_forced_template_candidate_graph,
        )

        pool = load_forced_template_candidate_pool(
            "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl"
        )
        selected_graph, candidate_graphs, selected_index = select_forced_template_candidate_graph(
            pool, "task_114", rank=2
        )

        self.assertEqual(len(pool), 34)
        self.assertEqual(len(candidate_graphs), 5)
        self.assertEqual(selected_index, 1)
        self.assertEqual(selected_graph.graph["selected_candidate_rank"], 2)
        self.assertIn("PN_Router", [selected_graph.nodes[node]["role"] for node in selected_graph.nodes])
        self.assertTrue(selected_graph.graph["forced_template_candidate"])

    def test_evaluate_aqua_cli_exposes_forced_template_options(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/evaluate_aqua.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--forced_template_candidate_jsonl", result.stdout)
        self.assertIn("--forced_template_candidate_rank", result.stdout)


if __name__ == "__main__":
    unittest.main()
