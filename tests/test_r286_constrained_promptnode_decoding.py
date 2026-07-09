import unittest


class TestR286ConstrainedPromptNodeDecoding(unittest.TestCase):
    def test_select_best_candidate_prefers_contract_ready_graph(self):
        from experiment.mmlu.r286_constrained_promptnode_decoding import (
            select_best_candidate,
        )

        weak = {
            "candidate_index": 0,
            "has_any_pn": True,
            "has_all_pn_roles": False,
            "has_pn_chain": False,
            "router_is_terminal": False,
            "promptedge_contract_ready": False,
            "pn_role_count": 1,
            "is_dag": True,
        }
        ready = {
            "candidate_index": 1,
            "has_any_pn": True,
            "has_all_pn_roles": True,
            "has_pn_chain": True,
            "router_is_terminal": True,
            "promptedge_contract_ready": True,
            "pn_role_count": 3,
            "is_dag": True,
        }

        selected = select_best_candidate([weak, ready])

        self.assertEqual(selected["candidate_index"], 1)
        self.assertTrue(selected["promptedge_contract_ready"])

    def test_select_best_candidate_uses_partial_structure_when_no_ready_graph_exists(self):
        from experiment.mmlu.r286_constrained_promptnode_decoding import (
            select_best_candidate,
        )

        no_pn = {
            "candidate_index": 0,
            "has_any_pn": False,
            "has_all_pn_roles": False,
            "has_pn_chain": False,
            "router_is_terminal": False,
            "promptedge_contract_ready": False,
            "pn_role_count": 0,
            "is_dag": True,
        }
        partial = {
            "candidate_index": 1,
            "has_any_pn": True,
            "has_all_pn_roles": True,
            "has_pn_chain": False,
            "router_is_terminal": False,
            "promptedge_contract_ready": False,
            "pn_role_count": 3,
            "is_dag": True,
        }

        selected = select_best_candidate([no_pn, partial])

        self.assertEqual(selected["candidate_index"], 1)
        self.assertFalse(selected["promptedge_contract_ready"])

    def test_summarize_selected_allows_run_id_for_followup_budgets(self):
        from experiment.mmlu.r286_constrained_promptnode_decoding import summarize_selected

        selected = [{"task_id": "t0", "promptedge_contract_ready": True, "is_dag": True}]
        candidates = [{"task_id": "t0", "promptedge_contract_ready": True}]

        summary = summarize_selected(selected, candidates, candidates_per_task=64, run_id="R287")

        self.assertEqual(summary["run_id"], "R287")
        self.assertEqual(summary["candidates_per_task"], 64)

    def test_describe_graph_persists_roles_and_edges_for_api_replay(self):
        import networkx as nx

        from experiment.mmlu.r286_constrained_promptnode_decoding import describe_graph

        graph = nx.DiGraph()
        graph.add_node(0, role="Mathematician")
        graph.add_node(1, role="PN_Memory")
        graph.add_edge(0, 1, label=1)

        record = describe_graph(graph)

        self.assertEqual(record["nodes"], [{"id": 0, "role": "Mathematician"}, {"id": 1, "role": "PN_Memory"}])
        self.assertEqual(record["edges"], [{"source": 0, "target": 1, "label": 1}])


if __name__ == "__main__":
    unittest.main()
