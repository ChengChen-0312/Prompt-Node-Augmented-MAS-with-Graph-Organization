import unittest
import subprocess
import sys


class OfflineUtilitySelectorTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/offline_utility_selector.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_extract_features_uses_runtime_votes_and_prompt_node_graphs(self):
        from experiment.aqua.offline_utility_selector import extract_selector_features

        result_sets = {
            "baseline": {
                "task_1": {
                    "task_id": "task_1",
                    "predicted_answer": "A",
                    "generated_graph": {"roles": ["Math Solver", "Programming Expert"]},
                }
            },
            "router": {
                "task_1": {
                    "task_id": "task_1",
                    "predicted_answer": "B",
                    "generated_graph": {"roles": ["Math Solver", "PN_Memory", "PN_Verifier"]},
                }
            },
            "candidate": {
                "task_1": {
                    "task_id": "task_1",
                    "predicted_answer": "B",
                    "generated_graph": {"roles": ["Math Solver", "PN_Router"]},
                    "candidate_graphs": [
                        {"roles": ["Math Solver"]},
                        {"roles": ["Math Solver", "PN_Memory"]},
                    ],
                }
            },
            "conservative": {"task_1": {"task_id": "task_1", "predicted_answer": "B"}},
            "calibrated": {"task_1": {"task_id": "task_1", "predicted_answer": "C"}},
            "ensemble": {
                "task_1": {
                    "task_id": "task_1",
                    "predicted_answer": "B",
                    "method_predictions": {
                        "baseline": "A",
                        "router": "B",
                        "candidate": "B",
                        "conservative": "B",
                        "calibrated": "C",
                    },
                    "method_order": [
                        "baseline",
                        "router",
                        "candidate",
                        "conservative",
                        "calibrated",
                    ],
                }
            },
        }

        features = extract_selector_features("task_1", result_sets)

        self.assertTrue(features["baseline_valid"])
        self.assertTrue(features["ensemble_valid"])
        self.assertTrue(features["baseline_disagrees_ensemble"])
        self.assertEqual(features["majority_prediction"], "B")
        self.assertEqual(features["majority_count"], 3)
        self.assertEqual(features["pn_supports_ensemble_count"], 3)
        self.assertTrue(features["candidate_selected_prompt_node"])
        self.assertTrue(features["candidate_any_prompt_node"])

    def test_train_best_rule_learns_prompt_node_majority_switch(self):
        from experiment.aqua.offline_utility_selector import apply_rule, train_best_rule

        records = [
            {
                "task_id": "fix",
                "true_answer": "B",
                "baseline_prediction": "A",
                "ensemble_prediction": "B",
                "features": {
                    "baseline_disagrees_ensemble": True,
                    "ensemble_valid": True,
                    "pn_supports_ensemble_count": 3,
                    "majority_count": 3,
                    "candidate_selected_prompt_node": True,
                },
            },
            {
                "task_id": "keep",
                "true_answer": "D",
                "baseline_prediction": "D",
                "ensemble_prediction": "D",
                "features": {
                    "baseline_disagrees_ensemble": False,
                    "ensemble_valid": True,
                    "pn_supports_ensemble_count": 1,
                    "majority_count": 4,
                    "candidate_selected_prompt_node": False,
                },
            },
            {
                "task_id": "avoid_harm",
                "true_answer": "C",
                "baseline_prediction": "C",
                "ensemble_prediction": "E",
                "features": {
                    "baseline_disagrees_ensemble": True,
                    "ensemble_valid": True,
                    "pn_supports_ensemble_count": 1,
                    "majority_count": 2,
                    "candidate_selected_prompt_node": False,
                },
            },
        ]

        rule = train_best_rule(records)

        self.assertEqual(rule["name"], "pn_support_ge_3")
        self.assertTrue(apply_rule(rule, records[0]["features"]))
        self.assertFalse(apply_rule(rule, records[1]["features"]))
        self.assertFalse(apply_rule(rule, records[2]["features"]))

    def test_build_selected_records_marks_source_without_gold_features(self):
        from experiment.aqua.offline_utility_selector import build_selected_records

        result_sets = {
            "baseline": {
                "task_1": {
                    "task_id": "task_1",
                    "question": "q",
                    "true_answer": "B",
                    "predicted_answer": "A",
                }
            },
            "ensemble": {
                "task_1": {
                    "task_id": "task_1",
                    "question": "q",
                    "true_answer": "B",
                    "predicted_answer": "B",
                    "method_predictions": {
                        "baseline": "A",
                        "router": "B",
                        "candidate": "B",
                        "conservative": "B",
                        "calibrated": "C",
                    },
                }
            },
        }

        records = build_selected_records(
            result_sets,
            ["task_1"],
            {"name": "pn_support_ge_3", "min_pn_support": 3},
        )

        self.assertEqual(records[0]["predicted_answer"], "B")
        self.assertEqual(records[0]["selected_source"], "ensemble")
        self.assertTrue(records[0]["is_solved"])
        self.assertNotIn("true_answer", records[0]["selector_features"])

    def test_extract_contract_consensus_features_reads_router_and_direct_majority(self):
        from experiment.aqua.offline_utility_selector import extract_contract_consensus_features

        record = {
            "agent_outputs": [
                {"node": 0, "role": "Math Solver", "outputs": ["The answer is B"]},
                {"node": 1, "role": "Programming Expert", "outputs": ["The answer is B"]},
                {
                    "node": 2,
                    "role": "PN_Router",
                    "outputs": [
                        "SUPPORTED_OPTION: B\n"
                        "BINDING_STATUS: EXACT_MATCH\n"
                        "FINAL_EVIDENCE_SUMMARY: verified option binding"
                    ],
                },
            ]
        }

        features = extract_contract_consensus_features(record)

        self.assertEqual(features["router_option"], "B")
        self.assertEqual(features["router_binding_status"], "EXACT_MATCH")
        self.assertEqual(features["direct_majority"], "B")
        self.assertEqual(features["direct_majority_count"], 2)
        self.assertTrue(features["router_matches_direct_majority"])

    def test_contract_consensus_rule_switches_only_on_router_direct_agreement(self):
        from experiment.aqua.offline_utility_selector import apply_contract_consensus_rule

        switch_prediction, switch_source = apply_contract_consensus_rule(
            baseline_prediction="A",
            ensemble_prediction="C",
            features={
                "router_option": "B",
                "direct_majority": "B",
                "direct_majority_count": 2,
                "router_matches_direct_majority": True,
            },
        )
        conflict_prediction, conflict_source = apply_contract_consensus_rule(
            baseline_prediction="A",
            ensemble_prediction="C",
            features={
                "router_option": "B",
                "direct_majority": "A",
                "direct_majority_count": 2,
                "router_matches_direct_majority": False,
            },
        )
        invalid_prediction, invalid_source = apply_contract_consensus_rule(
            baseline_prediction=None,
            ensemble_prediction="D",
            features={
                "router_option": "B",
                "direct_majority": "B",
                "direct_majority_count": 2,
                "router_matches_direct_majority": True,
            },
        )

        self.assertEqual((switch_prediction, switch_source), ("B", "router_contract"))
        self.assertEqual((conflict_prediction, conflict_source), ("A", "baseline"))
        self.assertEqual((invalid_prediction, invalid_source), ("D", "ensemble_invalid"))

    def test_extract_multi_contract_features_aggregates_across_methods(self):
        from experiment.aqua.offline_utility_selector import extract_multi_contract_features

        def method_record(option, direct_option="B"):
            return {
                "agent_outputs": [
                    {"node": 0, "role": "Math Solver", "outputs": [f"The answer is {direct_option}"]},
                    {"node": 1, "role": "Programming Expert", "outputs": [f"The answer is {direct_option}"]},
                    {
                        "node": 2,
                        "role": "PN_Router",
                        "outputs": [
                            f"SUPPORTED_OPTION: {option}\n"
                            "BINDING_STATUS: EXACT_MATCH\n"
                            "FINAL_EVIDENCE_SUMMARY: verified option binding"
                        ],
                    },
                ]
            }

        result_sets = {
            "router": {"task_1": method_record("B")},
            "calibrated": {"task_1": method_record("B")},
            "candidate": {"task_1": method_record("C", direct_option="A")},
        }

        features = extract_multi_contract_features(
            "task_1",
            result_sets,
            method_keys=["router", "calibrated", "candidate"],
        )

        self.assertEqual(features["strong_option_counts"], {"B": 2, "C": 1})
        self.assertEqual(features["direct_consensus_counts"], {"B": 2})
        self.assertEqual(features["method_features"]["router"]["router_option"], "B")

    def test_multi_contract_union_rule_uses_direct_union_and_strong_majority(self):
        from experiment.aqua.offline_utility_selector import apply_multi_contract_union_rule

        direct_prediction, direct_source = apply_multi_contract_union_rule(
            baseline_prediction="A",
            ensemble_prediction="D",
            features={
                "strong_option_counts": {"B": 2},
                "direct_consensus_counts": {"B": 2},
            },
        )
        majority_prediction, majority_source = apply_multi_contract_union_rule(
            baseline_prediction="A",
            ensemble_prediction="D",
            features={
                "strong_option_counts": {"C": 3, "E": 1},
                "direct_consensus_counts": {},
            },
        )
        tie_prediction, tie_source = apply_multi_contract_union_rule(
            baseline_prediction="A",
            ensemble_prediction="D",
            features={
                "strong_option_counts": {"B": 2, "C": 2},
                "direct_consensus_counts": {"B": 1, "C": 1},
            },
        )
        invalid_prediction, invalid_source = apply_multi_contract_union_rule(
            baseline_prediction=None,
            ensemble_prediction="E",
            features={
                "strong_option_counts": {"B": 2},
                "direct_consensus_counts": {"B": 2},
            },
        )

        self.assertEqual((direct_prediction, direct_source), ("B", "multi_contract_union"))
        self.assertEqual((majority_prediction, majority_source), ("C", "multi_contract_union"))
        self.assertEqual((tie_prediction, tie_source), ("A", "baseline"))
        self.assertEqual((invalid_prediction, invalid_source), ("E", "ensemble_invalid"))


if __name__ == "__main__":
    unittest.main()
