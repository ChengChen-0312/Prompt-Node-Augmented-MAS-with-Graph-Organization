import unittest


def _row(positive=True, slice_prefix="aqua_100"):
    return {
        "source_slice_prefix": slice_prefix,
        "selector_policy_input": {
            "slice_prefix": slice_prefix,
            "question": "Synthetic?",
            "candidate_method": "candidate",
            "score_margin_to_next": 5 if positive else 0,
            "has_margin_at_least_3": positive,
            "objective_prediction_differs_from_baseline": positive,
            "baseline_direct_votes_split": positive,
            "objective_top_score": 8 if positive else 1,
            "candidate_graph_observation": {
                "num_prompt_nodes": 3 if positive else 0,
                "num_prompt_node_edges": 4 if positive else 0,
                "has_promptnode_specs": positive,
                "has_promptnode_edge_permissions": positive,
                "prompt_node_role_counts": {"PN_Memory": 1, "PN_Verifier": 1, "PN_Router": 1}
                if positive
                else {},
            },
        },
        "positive_graph_target": positive,
    }


class R168PromptEdgeSelectorTests(unittest.TestCase):
    def test_selector_learns_synthetic_promptedge_boundary(self):
        from experiment.aqua.r168_promptedge_selector import (
            evaluate_selector,
            train_selector,
        )

        rows = [_row(True), _row(False), _row(False)]
        model = train_selector(rows, epochs=5, learning_rate=0.1)
        metrics = evaluate_selector(model, rows)

        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["positive_recall"], 1.0)

    def test_real_r166_rows_train_and_eval_without_forbidden_fields(self):
        from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows
        from experiment.aqua.r168_promptedge_selector import build_selector_summary

        rows = load_jsonl_rows(
            "experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl"
        )
        summary = build_selector_summary(rows)

        self.assertEqual(summary["source_rows"], 800)
        self.assertEqual(summary["train_rows"], 400)
        self.assertEqual(summary["eval_rows"], 400)
        self.assertEqual(summary["input_field_violations"], 0)
        self.assertGreaterEqual(summary["eval_metrics"]["accuracy"], 0.95)
        self.assertGreaterEqual(summary["eval_metrics"]["positive_recall"], 0.95)


if __name__ == "__main__":
    unittest.main()
