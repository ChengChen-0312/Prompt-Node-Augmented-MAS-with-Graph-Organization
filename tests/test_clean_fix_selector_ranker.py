import subprocess
import sys
import unittest


FORBIDDEN_INPUT_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "task_id",
    "source_task_id",
}


def _row(target_class="clean_fix_preserve_graph", slice_prefix="train"):
    positive = target_class == "clean_fix_preserve_graph"
    return {
        "source_slice_prefix": slice_prefix,
        "selector_policy_input": {
            "slice_prefix": slice_prefix,
            "question": "Synthetic question?",
            "candidate_method": "candidate",
            "label_free_objective_features": {
                "objective_reward": 10 if positive else 1,
                "score_margin_to_next": 4 if positive else None,
                "has_margin_at_least_3": positive,
                "score_components": {
                    "strong_contract": 4 if positive else 0,
                    "direct_agreement": 3 if positive else 0,
                    "direct_vote_support": 2,
                    "prompt_node_graph": 1 if positive else 0,
                    "conflict_penalty": 0,
                    "weak_contract_penalty": 0,
                },
            },
            "candidate_graph_observation": {
                "num_prompt_nodes": 3 if positive else 0,
                "num_prompt_node_edges": 4 if positive else 0,
                "prompt_node_role_counts": {"PN_Memory": 1, "PN_Verifier": 1, "PN_Router": 1}
                if positive
                else {},
                "prompt_node_edge_role_pairs": ["PN_Memory->PN_Verifier"] if positive else [],
                "has_promptnode_specs": positive,
                "has_promptnode_edge_permissions": positive,
            },
        },
        "clean_fix_distillation_target": {
            "target_class": target_class,
            "teacher_policy": "preserve_high_margin_promptnode_graph" if positive else "suppress",
        },
    }


class CleanFixSelectorRankerTests(unittest.TestCase):
    def test_feature_vector_excludes_forbidden_fields_and_encodes_promptnode_signal(self):
        from experiment.aqua.clean_fix_selector_ranker import FEATURE_NAMES, feature_vector, input_field_violations

        row = _row()
        row["selector_policy_input"]["task_id"] = "leaky"

        vector = feature_vector(row)

        self.assertEqual(len(vector), len(FEATURE_NAMES))
        self.assertFalse(FORBIDDEN_INPUT_FIELDS & set(FEATURE_NAMES))
        self.assertGreater(vector[FEATURE_NAMES.index("strong_contract")], 0)
        self.assertGreater(vector[FEATURE_NAMES.index("num_prompt_nodes")], 0)
        self.assertEqual(input_field_violations([row]), 1)

    def test_train_pointwise_selector_learns_synthetic_clean_fix_target(self):
        from experiment.aqua.clean_fix_selector_ranker import evaluate_selector, train_pointwise_selector

        rows = [
            _row("clean_fix_preserve_graph", "train"),
            _row("negative_graph_suppress", "train"),
            _row("ambiguous_or_low_margin_suppress", "train"),
        ]

        model = train_pointwise_selector(rows, epochs=5, learning_rate=0.1)
        metrics = evaluate_selector(model, rows)

        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["positive_recall"], 1.0)
        self.assertGreater(model["weights"]["strong_contract"], 0)

    def test_real_r077_rows_train_on_first100_eval_on_next100(self):
        from experiment.aqua.clean_fix_selector_ranker import build_selector_summary

        summary = build_selector_summary()

        self.assertEqual(summary["source_rows"], 800)
        self.assertEqual(summary["train_rows"], 400)
        self.assertEqual(summary["eval_rows"], 400)
        self.assertEqual(summary["input_field_violations"], 0)
        self.assertGreaterEqual(summary["train_metrics"]["accuracy"], 0.95)
        self.assertGreaterEqual(summary["eval_metrics"]["accuracy"], 0.95)
        self.assertGreaterEqual(summary["eval_metrics"]["positive_recall"], 0.95)
        self.assertIn("target agreement", summary["claim_boundary"])

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/clean_fix_selector_ranker.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
