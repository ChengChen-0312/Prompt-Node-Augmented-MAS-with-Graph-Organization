import unittest


class TestR288ConstrainedGraphAPIReplay(unittest.TestCase):
    def test_manifest_to_nx_preserves_nodes_edges_and_constraints(self):
        from experiment.mmlu.r288_constrained_graph_api_replay import manifest_to_nx

        manifest = {
            "nodes": [{"id": 0, "role": "Mathematician"}, {"id": 1, "role": "PN_Router"}],
            "edges": [{"source": 0, "target": 1, "label": 1}],
        }

        graph = manifest_to_nx(manifest)

        self.assertEqual(graph.nodes[0]["role"], "Mathematician")
        self.assertIn("math", graph.nodes[0]["constraint"].lower())
        self.assertEqual(list(graph.edges()), [(0, 1)])
        self.assertEqual(graph.edges[0, 1]["label"], 1)

    def test_summarize_records_reports_accuracy_and_cost(self):
        from experiment.mmlu.r288_constrained_graph_api_replay import summarize_records

        rows = [
            {"is_correct": True, "api_error": ""},
            {"is_correct": False, "api_error": ""},
            {"is_correct": None, "api_error": "timeout"},
        ]

        summary = summarize_records(rows, api_cost=1.25, prompt_tokens=100, completion_tokens=20)

        self.assertEqual(summary["records"], 3)
        self.assertEqual(summary["evaluated_records"], 2)
        self.assertEqual(summary["api_errors"], 1)
        self.assertEqual(summary["correct"], 1)
        self.assertEqual(summary["accuracy"], 0.5)
        self.assertEqual(summary["api_cost"], 1.25)


if __name__ == "__main__":
    unittest.main()
