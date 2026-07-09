import subprocess
import sys
import unittest


DISALLOWED_FIELDS = {
    "true_answer",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "r035_selected_prediction",
    "r035_selected_source",
}


class GraphObjectivePairwiseExportTests(unittest.TestCase):
    def test_build_pairwise_preferences_pairs_preferred_against_same_task_negatives(self):
        from experiment.aqua.graph_objective_pairwise_export import build_pairwise_preferences

        rows = [
            {
                "task_id": "task_x",
                "slice_prefix": "synthetic",
                "candidate_method": "candidate",
                "objective_score": 10,
                "score_components": {"strong_contract": 4},
                "training_target": "preferred_graph",
                "router_option": "B",
                "has_prompt_node_graph": True,
            },
            {
                "task_id": "task_x",
                "slice_prefix": "synthetic",
                "candidate_method": "router",
                "objective_score": 6,
                "score_components": {"strong_contract": 0},
                "training_target": "non_preferred_graph",
                "router_option": "C",
                "has_prompt_node_graph": True,
            },
            {
                "task_id": "task_x",
                "slice_prefix": "synthetic",
                "candidate_method": "calibrated",
                "objective_score": 2,
                "score_components": {"strong_contract": 0},
                "training_target": "low_margin_top",
                "router_option": "D",
                "has_prompt_node_graph": False,
            },
        ]

        pairs, summary = build_pairwise_preferences(rows)

        self.assertEqual(len(pairs), 2)
        self.assertEqual(summary["tasks_with_preferences"], 1)
        self.assertEqual(summary["pairwise_rows"], 2)
        self.assertEqual(pairs[0]["positive_method"], "candidate")
        self.assertEqual(pairs[0]["negative_method"], "router")
        self.assertEqual(pairs[0]["score_delta"], 4)
        self.assertEqual(pairs[1]["negative_method"], "calibrated")
        self.assertFalse(DISALLOWED_FIELDS & set(pairs[0]))

    def test_build_pairwise_preferences_skips_tasks_without_preferred_graph(self):
        from experiment.aqua.graph_objective_pairwise_export import build_pairwise_preferences

        rows = [
            {
                "task_id": "task_tie",
                "candidate_method": "router",
                "objective_score": 9,
                "training_target": "multi_view_tie",
            },
            {
                "task_id": "task_tie",
                "candidate_method": "candidate",
                "objective_score": 9,
                "training_target": "multi_view_tie",
            },
        ]

        pairs, summary = build_pairwise_preferences(rows)

        self.assertEqual(pairs, [])
        self.assertEqual(summary["tasks_with_preferences"], 0)
        self.assertEqual(summary["skipped_tasks_without_preferred"], 1)

    def test_real_first200_pairwise_export_has_no_outcome_fields(self):
        from experiment.aqua.graph_objective_pairwise_export import (
            build_pairwise_preferences,
            load_jsonl_rows,
        )

        rows = load_jsonl_rows("experiment/aqua/aqua_first200_graph_objective_training_rows.jsonl")
        pairs, summary = build_pairwise_preferences(rows)

        self.assertEqual(summary["source_rows"], 800)
        self.assertEqual(summary["tasks_with_preferences"], 76)
        self.assertEqual(summary["pairwise_rows"], 228)
        self.assertEqual(summary["outcome_field_violations"], 0)
        self.assertTrue(all(not (DISALLOWED_FIELDS & set(pair)) for pair in pairs))

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/graph_objective_pairwise_export.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
