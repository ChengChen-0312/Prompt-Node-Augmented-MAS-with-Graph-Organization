import unittest

import networkx as nx


def _positive_selector_input():
    return {
        "question": "Synthetic?",
        "candidate_method": "candidate",
        "objective_bucket": "preferred_graph",
        "score_margin_to_next": 5,
        "has_margin_at_least_3": True,
        "objective_prediction_differs_from_baseline": True,
        "baseline_direct_votes_split": False,
        "objective_top_score": 8,
        "candidate_graph_observation": {
            "num_prompt_nodes": 3,
            "num_prompt_node_edges": 4,
            "has_promptnode_specs": True,
            "has_promptnode_edge_permissions": True,
            "prompt_node_role_counts": {
                "PN_Memory": 1,
                "PN_Verifier": 1,
                "PN_Router": 1,
            },
        },
    }


def _promptedge_graph():
    graph = nx.DiGraph()
    graph.add_node(0, role="Math Solver")
    graph.add_node(1, role="Programming Expert")
    graph.add_node(2, role="PN_Memory")
    graph.add_node(3, role="PN_Verifier")
    graph.add_node(4, role="PN_Router")
    graph.add_edges_from([(0, 1), (0, 2), (1, 2), (2, 3), (3, 4)])
    return graph


class R171SelectorGatedPromptEdgeSmokeTests(unittest.TestCase):
    def test_graph_contract_requires_promptedge_path_and_dag(self):
        from experiment.aqua.r171_selector_gated_promptedge_smoke import (
            promptedge_contract_evidence,
        )

        evidence = promptedge_contract_evidence(_promptedge_graph())

        self.assertTrue(evidence["contract_passed"])
        self.assertEqual(evidence["prompt_edge_type_counts"]["write_memory"], 2)
        self.assertEqual(evidence["prompt_edge_type_counts"]["verify_contract"], 1)
        self.assertEqual(evidence["prompt_edge_type_counts"]["forward_verified"], 1)

        cyclic = _promptedge_graph()
        cyclic.add_edge(4, 0)
        cyclic_evidence = promptedge_contract_evidence(cyclic)

        self.assertFalse(cyclic_evidence["contract_passed"])
        self.assertFalse(cyclic_evidence["is_dag"])

    def test_selector_gate_rejects_forbidden_policy_input(self):
        from experiment.aqua.r171_selector_gated_promptedge_smoke import (
            build_selector_decision,
        )

        model = {
            "weights": {
                "bias": 1.0,
                "score_margin_to_next": 1.0,
                "num_prompt_nodes": 1.0,
            },
            "threshold": 0.0,
        }
        policy_input = _positive_selector_input()
        policy_input["task_id"] = "task_108"

        decision = build_selector_decision(model, policy_input)

        self.assertFalse(decision["selector_passed"])
        self.assertEqual(decision["selector_action"], "fallback_to_arg")
        self.assertEqual(decision["selector_input_field_violations"], 1)

    def test_build_selected_record_switches_only_when_selector_and_contract_pass(self):
        from experiment.aqua.r171_selector_gated_promptedge_smoke import (
            build_selected_record,
        )

        baseline = {
            "task_id": "task_x",
            "question": "Q?",
            "true_answer": "B",
            "predicted_answer": "A",
            "raw_response": "The answer is A",
            "is_solved": False,
        }
        promptedge = {
            "task_id": "task_x",
            "question": "Q?",
            "true_answer": "B",
            "predicted_answer": "B",
            "raw_response": "The answer is B",
            "is_solved": True,
            "generated_graph": {
                "roles": ["Math Solver", "PN_Memory", "PN_Verifier", "PN_Router"],
                "edges": [[0, 1], [1, 2], [2, 3]],
            },
        }
        selector_decision = {
            "selector_passed": True,
            "selector_action": "run_promptedge",
            "selector_score": 3.0,
            "selector_threshold": 0.0,
            "selector_input_field_violations": 0,
        }
        contract = {
            "contract_passed": True,
            "is_dag": True,
            "has_required_prompt_roles": True,
            "has_required_promptedge_path": True,
            "prompt_edge_type_counts": {
                "write_memory": 1,
                "verify_contract": 1,
                "forward_verified": 1,
            },
        }

        selected = build_selected_record(
            baseline,
            promptedge,
            selector_decision,
            contract,
            policy_input={
                **_positive_selector_input(),
                "selector_prior": {"dominant_selective_action": "switch_critical_insert"},
            },
        )

        self.assertEqual(selected["selected_source"], "selector_gated_promptedge")
        self.assertTrue(selected["is_solved"])
        self.assertTrue(selected["fix"])
        self.assertFalse(selected["harm"])

        failed_contract = dict(contract, contract_passed=False)
        fallback = build_selected_record(
            baseline,
            promptedge,
            selector_decision,
            failed_contract,
            policy_input=_positive_selector_input(),
        )

        self.assertEqual(fallback["selected_source"], "baseline")
        self.assertEqual(fallback["predicted_answer"], "A")

    def test_preserve_safe_prior_cannot_override_with_valid_promptedge_option(self):
        from experiment.aqua.r171_selector_gated_promptedge_smoke import (
            build_selected_record,
        )

        baseline = {
            "task_id": "task_x",
            "question": "Q?",
            "true_answer": "A",
            "predicted_answer": "A",
            "raw_response": "The answer is A",
            "is_solved": True,
        }
        promptedge = {
            "task_id": "task_x",
            "question": "Q?",
            "true_answer": "A",
            "predicted_answer": "B",
            "raw_response": "The answer is B",
            "is_solved": False,
        }
        selector_decision = {
            "selector_passed": True,
            "selector_action": "run_promptedge",
            "selector_score": 3.0,
            "selector_threshold": 0.0,
            "selector_input_field_violations": 0,
        }
        contract = {
            "contract_passed": True,
            "is_dag": True,
            "has_required_prompt_roles": True,
            "has_required_promptedge_path": True,
            "prompt_edge_type_counts": {
                "write_memory": 1,
                "verify_contract": 1,
                "forward_verified": 1,
            },
        }

        selected = build_selected_record(
            baseline,
            promptedge,
            selector_decision,
            contract,
            policy_input={
                **_positive_selector_input(),
                "selector_prior": {"dominant_selective_action": "preserve_safe_insert"},
            },
        )

        self.assertEqual(selected["selected_source"], "baseline")
        self.assertEqual(selected["predicted_answer"], "A")
        self.assertEqual(
            selected["runtime_fallback_reason"],
            "selector_prior_preserve_safe_not_switch_critical",
        )

    def test_promptedge_abstention_falls_back_even_when_selector_and_contract_pass(self):
        from experiment.aqua.r171_selector_gated_promptedge_smoke import (
            build_selected_record,
        )

        baseline = {
            "task_id": "task_x",
            "question": "Q?",
            "true_answer": "E",
            "predicted_answer": "E",
            "raw_response": "The answer is E",
            "is_solved": True,
        }
        promptedge = {
            "task_id": "task_x",
            "question": "Q?",
            "true_answer": "E",
            "predicted_answer": "None.",
            "raw_response": "no valid option is supported",
            "is_solved": False,
        }
        selector_decision = {
            "selector_passed": True,
            "selector_action": "run_promptedge",
            "selector_score": 3.0,
            "selector_threshold": 0.0,
            "selector_input_field_violations": 0,
        }
        contract = {
            "contract_passed": True,
            "is_dag": True,
            "has_required_prompt_roles": True,
            "has_required_promptedge_path": True,
            "prompt_edge_type_counts": {
                "write_memory": 1,
                "verify_contract": 1,
                "forward_verified": 1,
            },
        }

        selected = build_selected_record(
            baseline,
            promptedge,
            selector_decision,
            contract,
            policy_input=_positive_selector_input(),
        )

        self.assertEqual(selected["selected_source"], "baseline")
        self.assertEqual(selected["predicted_answer"], "E")
        self.assertFalse(selected["harm"])
        self.assertEqual(
            selected["runtime_fallback_reason"],
            "promptedge_abstained_or_invalid_option",
        )


if __name__ == "__main__":
    unittest.main()
