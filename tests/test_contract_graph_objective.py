import unittest


class ContractGraphObjectiveTests(unittest.TestCase):
    def test_score_contract_features_rewards_strong_direct_agreement_and_penalizes_conflict(self):
        from experiment.aqua.contract_graph_objective import score_contract_features

        score = score_contract_features(
            {
                "router_option": "B",
                "strong_router_contract_count": 1,
                "direct_majority": "B",
                "direct_majority_count": 2,
                "direct_valid_vote_count": 2,
                "router_matches_direct_majority": True,
                "router_conflicts_with_direct_majority": False,
                "all_router_contracts_weak": False,
            },
            has_prompt_node_graph=True,
        )
        conflict = score_contract_features(
            {
                "router_option": "C",
                "strong_router_contract_count": 1,
                "direct_majority": "A",
                "direct_majority_count": 3,
                "direct_valid_vote_count": 3,
                "router_matches_direct_majority": False,
                "router_conflicts_with_direct_majority": True,
                "all_router_contracts_weak": False,
            },
            has_prompt_node_graph=True,
        )

        self.assertEqual(score["score"], 10)
        self.assertEqual(score["components"]["strong_contract"], 4)
        self.assertEqual(conflict["score"], 4)
        self.assertEqual(conflict["components"]["conflict_penalty"], -4)

    def test_rank_task_variants_returns_sorted_label_free_scores(self):
        from experiment.aqua.contract_graph_objective import rank_task_variants

        def record(role, option, direct):
            return {
                "generated_graph": {"roles": ["Math Solver", role]},
                "agent_outputs": [
                    {"node": 0, "role": "Math Solver", "outputs": [f"The answer is {direct}"]},
                    {"node": 1, "role": "Programming Expert", "outputs": [f"The answer is {direct}"]},
                    {
                        "node": 2,
                        "role": "PN_Router",
                        "outputs": [
                            f"SUPPORTED_OPTION: {option}\n"
                            "BINDING_STATUS: EXACT_MATCH\n"
                            "FINAL_EVIDENCE_SUMMARY: verified"
                        ],
                    },
                ],
                "predicted_answer": option,
                "true_answer": "A",
            }

        ranked = rank_task_variants(
            "task_x",
            {
                "router": {"task_x": record("PN_Router", "B", "B")},
                "candidate": {"task_x": record("PN_Router", "C", "A")},
            },
            method_keys=["router", "candidate"],
        )

        self.assertEqual(ranked[0]["method_key"], "router")
        self.assertNotIn("true_answer", ranked[0])
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])

    def test_build_objective_summary_counts_unique_top_and_ties(self):
        from experiment.aqua.contract_graph_objective import build_objective_summary

        records = [
            {
                "task_id": "a",
                "r035_selected_source": "multi_contract_union",
                "r035_selected_prediction": "B",
                "ranked_variants": [
                    {"method_key": "router", "score": 10, "router_option": "B"},
                    {"method_key": "candidate", "score": 4, "router_option": "A"},
                ],
            },
            {
                "task_id": "b",
                "ranked_variants": [
                    {"method_key": "router", "score": 5, "router_option": "C"},
                    {"method_key": "candidate", "score": 5, "router_option": "C"},
                ],
            },
        ]

        summary = build_objective_summary(records)

        self.assertEqual(summary["total_tasks"], 2)
        self.assertEqual(summary["positive_top_score_tasks"], 2)
        self.assertEqual(summary["unique_top_method_distribution"], {"router": 1})
        self.assertEqual(summary["top_score_ties"], 1)
        self.assertEqual(summary["r035_pure_switch_tasks"], 1)
        self.assertEqual(summary["r035_switch_top_option_agreement"], 1)

    def test_objective_selector_switches_only_on_unique_valid_top_option(self):
        from experiment.aqua.contract_graph_objective import select_objective_guided_prediction

        switch_prediction, switch_source = select_objective_guided_prediction(
            baseline_prediction="A",
            ranked_variants=[
                {"method_key": "router", "score": 10, "router_option": "B", "predicted_answer": "B"},
                {"method_key": "candidate", "score": 4, "router_option": "C", "predicted_answer": "C"},
            ],
        )
        keep_prediction, keep_source = select_objective_guided_prediction(
            baseline_prediction="A",
            ranked_variants=[
                {"method_key": "router", "score": 10, "router_option": "B", "predicted_answer": "B"},
                {"method_key": "candidate", "score": 10, "router_option": "C", "predicted_answer": "C"},
            ],
        )

        self.assertEqual((switch_prediction, switch_source), ("B", "objective_top"))
        self.assertEqual((keep_prediction, keep_source), ("A", "baseline"))

    def test_objective_selector_respects_min_score_margin(self):
        from experiment.aqua.contract_graph_objective import select_objective_guided_prediction

        low_margin_prediction, low_margin_source = select_objective_guided_prediction(
            baseline_prediction="A",
            ranked_variants=[
                {"method_key": "router", "score": 10, "router_option": "B", "predicted_answer": "B"},
                {"method_key": "candidate", "score": 9, "router_option": "C", "predicted_answer": "C"},
            ],
            min_score_margin=2,
        )
        enough_margin_prediction, enough_margin_source = select_objective_guided_prediction(
            baseline_prediction="A",
            ranked_variants=[
                {"method_key": "router", "score": 10, "router_option": "B", "predicted_answer": "B"},
                {"method_key": "candidate", "score": 8, "router_option": "C", "predicted_answer": "C"},
            ],
            min_score_margin=2,
        )

        self.assertEqual((low_margin_prediction, low_margin_source), ("A", "baseline"))
        self.assertEqual((enough_margin_prediction, enough_margin_source), ("B", "objective_top"))

    def test_build_objective_selector_records_marks_fixes_and_harms(self):
        from experiment.aqua.contract_graph_objective import (
            summarize_selector_records,
            summarize_selector_records_with_audit,
        )

        records = [
            {
                "task_id": "fix",
                "true_answer": "B",
                "baseline_prediction": "A",
                "predicted_answer": "B",
                "selected_source": "objective_top",
            },
            {
                "task_id": "harm",
                "true_answer": "C",
                "baseline_prediction": "C",
                "predicted_answer": "A",
                "selected_source": "objective_top",
            },
            {
                "task_id": "keep",
                "true_answer": "D",
                "baseline_prediction": "D",
                "predicted_answer": "D",
                "selected_source": "baseline",
            },
        ]

        summary = summarize_selector_records(records)

        self.assertEqual(summary["overall"], "2/3")
        self.assertEqual(summary["baseline"], "2/3")
        self.assertEqual(summary["delta_vs_baseline"], 0)
        self.assertEqual(summary["fix_harm"], "1/1")
        self.assertEqual(summary["switches"], 2)

        audit_summary = summarize_selector_records_with_audit(
            records,
            {"fix": "clean", "harm": "noisy", "keep": "clean"},
        )
        self.assertEqual(audit_summary["clean"], "2/2")
        self.assertEqual(audit_summary["noisy_or_ambiguous"], "0/1")
        self.assertEqual(audit_summary["clean_fix_harm"], "1/0")
        self.assertEqual(audit_summary["noisy_fix_harm"], "0/1")


if __name__ == "__main__":
    unittest.main()
