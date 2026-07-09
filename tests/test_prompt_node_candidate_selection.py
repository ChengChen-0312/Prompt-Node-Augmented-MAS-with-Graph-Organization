import os
import sys
import unittest
from unittest import mock

import networkx as nx


class PromptNodeCandidateSelectionTests(unittest.TestCase):
    def test_generate_graph_forwards_num_samples_to_model(self):
        from experiment.utils import generate_graph

        class FakeModel:
            def __init__(self):
                self.sample_kwargs = None

            def sample(self, **kwargs):
                self.sample_kwargs = kwargs
                graphs = []
                for i in range(kwargs["num_samples"]):
                    graph = nx.DiGraph()
                    graph.add_node(0, role="Math Solver")
                    graph.graph["candidate_id"] = i
                    graphs.append(graph)
                return graphs

        model = FakeModel()
        graphs = generate_graph(
            model,
            task_embedding=None,
            role_constraints_dict={"Math Solver": "solve"},
            question_id="q0",
            num_samples=3,
            batch_size=1,
        )

        self.assertEqual(model.sample_kwargs["num_samples"], 3)
        self.assertEqual(model.sample_kwargs["batch_size"], 1)
        self.assertEqual(len(graphs), 3)
        self.assertEqual(graphs[2].graph["candidate_id"], 2)

    def test_selector_prefers_balanced_prompt_node_graph(self):
        from experiment.aqua.prompt_node_graph import (
            select_prompt_node_candidate_graph,
            score_prompt_node_candidate_graph,
        )

        weak = nx.DiGraph()
        weak.add_node(0, role="Math Solver")
        weak.add_node(1, role="Math Solver")
        weak.add_edge(0, 1, label=1)

        balanced = nx.DiGraph()
        for idx, role in enumerate([
            "Math Solver",
            "Programming Expert",
            "Inspector",
            "PN_Memory",
            "PN_Verifier",
            "PN_Router",
        ]):
            balanced.add_node(idx, role=role)
        balanced.add_edges_from([(0, 3), (1, 3), (3, 4), (4, 5), (2, 5)])

        weak_score = score_prompt_node_candidate_graph(weak)
        balanced_score = score_prompt_node_candidate_graph(balanced)
        selected, scored = select_prompt_node_candidate_graph([weak, balanced])

        self.assertGreater(balanced_score["score"], weak_score["score"])
        self.assertIs(selected, balanced)
        self.assertEqual(scored[1]["candidate_index"], 1)
        self.assertGreater(scored[1]["pn_coverage"], scored[0]["pn_coverage"])

    def test_evaluate_cli_and_candidate_metadata(self):
        aqua_dir = os.path.join(os.getcwd(), "experiment", "aqua")
        if aqua_dir not in sys.path:
            sys.path.insert(0, aqua_dir)

        from experiment.aqua.evaluate_aqua import (
            describe_candidate_graphs,
            parse_args,
        )

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver")
        scored = [{
            "candidate_index": 0,
            "score": 1.25,
            "roles": ["Math Solver"],
        }]

        metadata = describe_candidate_graphs([graph], selected_index=0, scored_candidates=scored)
        self.assertEqual(metadata["selected_candidate_index"], 0)
        self.assertEqual(metadata["candidate_graphs"][0]["score"], 1.25)
        self.assertEqual(metadata["candidate_graphs"][0]["roles"], ["Math Solver"])

        with mock.patch.object(
            sys,
            "argv",
            ["evaluate_aqua.py", "--num_candidate_graphs", "4"],
        ):
            args = parse_args()
        self.assertEqual(args.num_candidate_graphs, 4)


if __name__ == "__main__":
    unittest.main()
