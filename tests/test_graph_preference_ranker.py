import subprocess
import sys
import unittest


FORBIDDEN_FEATURE_NAMES = {
    "objective_score",
    "predicted_answer",
    "router_option",
    "true_answer",
    "audit_label",
    "is_solved",
}


def _pair(task_id, slice_prefix, pos_components, neg_components):
    return {
        "task_id": task_id,
        "slice_prefix": slice_prefix,
        "positive": {
            "score_components": pos_components,
            "strong_router_contract_count": 1,
            "router_matches_direct_majority": True,
            "has_prompt_node_graph": True,
            "objective_score": sum(pos_components.values()),
            "predicted_answer": "B",
        },
        "negative": {
            "score_components": neg_components,
            "strong_router_contract_count": 0,
            "router_matches_direct_majority": False,
            "has_prompt_node_graph": False,
            "objective_score": sum(neg_components.values()),
            "predicted_answer": "C",
        },
    }


class GraphPreferenceRankerTests(unittest.TestCase):
    def test_pair_feature_diff_excludes_answer_and_outcome_fields(self):
        from experiment.aqua.graph_preference_ranker import FEATURE_NAMES, pair_feature_diff

        pair = _pair(
            "task_x",
            "synthetic",
            {"strong_contract": 4, "direct_agreement": 3},
            {"strong_contract": 0, "direct_agreement": 0},
        )

        diff = pair_feature_diff(pair)

        self.assertEqual(len(diff), len(FEATURE_NAMES))
        self.assertFalse(FORBIDDEN_FEATURE_NAMES & set(FEATURE_NAMES))
        self.assertGreater(diff[FEATURE_NAMES.index("strong_contract")], 0)
        self.assertGreater(diff[FEATURE_NAMES.index("router_matches_direct_majority")], 0)

    def test_train_pairwise_ranker_learns_synthetic_preferences(self):
        from experiment.aqua.graph_preference_ranker import evaluate_ranker, train_pairwise_ranker

        pairs = [
            _pair(
                "task_a",
                "train",
                {"strong_contract": 4, "direct_agreement": 3, "direct_vote_support": 2},
                {"strong_contract": 0, "direct_agreement": 0, "direct_vote_support": 1},
            ),
            _pair(
                "task_b",
                "train",
                {"strong_contract": 4, "direct_agreement": 3, "prompt_node_graph": 1},
                {"strong_contract": 0, "direct_agreement": 0, "weak_contract_penalty": -2},
            ),
        ]

        model = train_pairwise_ranker(pairs, epochs=5, learning_rate=0.1)
        metrics = evaluate_ranker(model, pairs)

        self.assertEqual(metrics["correct_pairs"], 2)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertGreater(model["weights"]["strong_contract"], 0)
        self.assertGreater(model["weights"]["direct_agreement"], 0)

    def test_real_first200_train_eval_summary_is_label_free(self):
        from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows
        from experiment.aqua.graph_preference_ranker import build_ranker_summary

        pairs = load_jsonl_rows("experiment/aqua/aqua_first200_graph_objective_pairwise_preferences.jsonl")
        summary = build_ranker_summary(pairs, train_slice="aqua_100", eval_slice="aqua_next100")

        self.assertEqual(summary["train_pairs"], 123)
        self.assertEqual(summary["eval_pairs"], 105)
        self.assertEqual(summary["outcome_field_violations"], 0)
        self.assertGreaterEqual(summary["train_accuracy"], 0.9)
        self.assertGreaterEqual(summary["eval_accuracy"], 0.9)
        self.assertFalse(FORBIDDEN_FEATURE_NAMES & set(summary["feature_names"]))

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/graph_preference_ranker.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
