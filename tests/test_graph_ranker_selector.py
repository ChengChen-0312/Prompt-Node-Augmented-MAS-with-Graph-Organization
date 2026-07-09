import subprocess
import sys
import unittest


FORBIDDEN_SELECTOR_FIELDS = {
    "objective_score",
    "predicted_answer",
    "router_option",
    "true_answer",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
}


def _variant(method, components, router_option="B", prediction="B", strong_count=1, direct_match=True):
    return {
        "method_key": method,
        "method_index": 0,
        "score": sum(components.values()),
        "score_components": components,
        "router_option": router_option,
        "direct_majority": router_option,
        "router_matches_direct_majority": direct_match,
        "strong_router_contract_count": strong_count,
        "has_prompt_node_graph": bool(components.get("prompt_node_graph", 0)),
        "predicted_answer": prediction,
        "objective_score": sum(components.values()),
        "true_answer": prediction,
        "is_solved": True,
    }


def _model():
    return {
        "weights": {
            "strong_contract": 0.4,
            "direct_agreement": 0.3,
            "direct_vote_support": 0.0,
            "prompt_node_graph": 0.0,
            "conflict_penalty": 0.0,
            "weak_contract_penalty": 0.2,
            "strong_router_contract_count": 0.1,
            "router_matches_direct_majority": 0.1,
            "has_prompt_node_graph": 0.0,
        }
    }


class GraphRankerSelectorTests(unittest.TestCase):
    def test_selector_features_exclude_answers_and_outcomes(self):
        from experiment.aqua.graph_ranker_selector import FEATURE_NAMES, score_variant, selector_features

        variant = _variant(
            "candidate",
            {"strong_contract": 4, "direct_agreement": 3, "prompt_node_graph": 1},
            router_option="C",
            prediction="C",
        )

        features = selector_features(variant)
        score = score_variant(_model(), variant)

        self.assertEqual(set(features), set(FEATURE_NAMES))
        self.assertFalse(FORBIDDEN_SELECTOR_FIELDS & set(features))
        self.assertGreater(features["strong_contract"], 0)
        self.assertGreater(score, 0)

    def test_select_ranker_guided_prediction_requires_unique_valid_top_with_margin(self):
        from experiment.aqua.graph_ranker_selector import select_ranker_guided_prediction

        high = _variant(
            "candidate",
            {"strong_contract": 4, "direct_agreement": 3, "prompt_node_graph": 1},
            router_option="B",
            prediction="B",
        )
        low = _variant(
            "router",
            {"direct_vote_support": 1},
            router_option=None,
            prediction="C",
            strong_count=0,
            direct_match=False,
        )

        selected, source, selected_method, selected_score, margin = select_ranker_guided_prediction(
            "A",
            [high, low],
            _model(),
            min_ranker_score=0.1,
            min_ranker_margin=0.1,
        )

        self.assertEqual(selected, "B")
        self.assertEqual(source, "ranker_top")
        self.assertEqual(selected_method, "candidate")
        self.assertGreater(selected_score, 0)
        self.assertGreater(margin, 0)

        tie_a = _variant(
            "candidate",
            {"strong_contract": 4, "direct_agreement": 3},
            router_option="B",
            prediction="B",
        )
        tie_b = _variant(
            "calibrated",
            {"strong_contract": 4, "direct_agreement": 3},
            router_option="C",
            prediction="C",
        )
        tied_selected, tied_source, _, _, tied_margin = select_ranker_guided_prediction(
            "A",
            [tie_a, tie_b],
            _model(),
            min_ranker_score=0.1,
            min_ranker_margin=0.1,
        )

        self.assertEqual(tied_selected, "A")
        self.assertEqual(tied_source, "baseline")
        self.assertEqual(tied_margin, 0.0)

    def test_summarize_ranker_selector_records_reports_fix_harm_and_slices(self):
        from experiment.aqua.graph_ranker_selector import summarize_ranker_selector_records

        records = [
            {
                "slice_prefix": "train",
                "true_answer": "B",
                "baseline_prediction": "A",
                "predicted_answer": "B",
                "selected_source": "ranker_top",
                "selector_features": {"strong_contract": 4},
            },
            {
                "slice_prefix": "train",
                "true_answer": "A",
                "baseline_prediction": "A",
                "predicted_answer": "B",
                "selected_source": "ranker_top",
                "selector_features": {"strong_contract": 4},
            },
            {
                "slice_prefix": "eval",
                "true_answer": "C",
                "baseline_prediction": "C",
                "predicted_answer": "C",
                "selected_source": "baseline",
                "selector_features": {"strong_contract": 0},
            },
        ]

        summary = summarize_ranker_selector_records(records)

        self.assertEqual(summary["overall"]["overall"], "2/3")
        self.assertEqual(summary["overall"]["baseline"], "2/3")
        self.assertEqual(summary["overall"]["fix_harm"], "1/1")
        self.assertEqual(summary["slice_summaries"]["train"]["fix_harm"], "1/1")
        self.assertEqual(summary["slice_summaries"]["eval"]["fix_harm"], "0/0")
        self.assertEqual(summary["outcome_field_violations"], 0)

    def test_real_first200_selector_summary_is_label_free_at_selection_time(self):
        from experiment.aqua.graph_ranker_selector import (
            build_ranker_selector_records,
            load_objective_records,
            load_ranker_model,
            summarize_ranker_selector_records,
        )

        objective_records = load_objective_records(
            "experiment/aqua/res_logs/aqua_first200_contract_graph_objective_summary.json"
        )
        model = load_ranker_model("experiment/aqua/res_logs/aqua_first200_graph_preference_ranker_summary.json")
        records = build_ranker_selector_records(
            objective_records,
            model,
            min_ranker_score=0.1,
            min_ranker_margin=0.1,
        )
        summary = summarize_ranker_selector_records(records)

        self.assertEqual(len(records), 200)
        self.assertEqual(summary["overall"]["total_tasks"], 200)
        self.assertIn("aqua_100", summary["slice_summaries"])
        self.assertIn("aqua_next100", summary["slice_summaries"])
        self.assertEqual(summary["outcome_field_violations"], 0)
        self.assertFalse(FORBIDDEN_SELECTOR_FIELDS & set(summary["feature_names"]))
        self.assertTrue(all("selector_features" in record for record in records))

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/graph_ranker_selector.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
