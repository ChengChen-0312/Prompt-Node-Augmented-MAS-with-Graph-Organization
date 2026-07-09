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


class GraphObjectiveTrainingExportTests(unittest.TestCase):
    def test_build_training_rows_marks_margin_target_without_outcome_fields(self):
        from experiment.aqua.graph_objective_training_export import build_training_rows

        records = [
            {
                "task_id": "task_x",
                "slice_prefix": "synthetic",
                "true_answer": "B",
                "baseline_prediction": "A",
                "ranked_variants": [
                    {
                        "method_key": "candidate",
                        "score": 10,
                        "score_components": {"strong_contract": 4, "direct_agreement": 3},
                        "router_option": "B",
                        "direct_majority": "B",
                        "strong_router_contract_count": 1,
                        "has_prompt_node_graph": True,
                        "predicted_answer": "B",
                    },
                    {
                        "method_key": "router",
                        "score": 6,
                        "score_components": {"strong_contract": 4, "direct_agreement": 0},
                        "router_option": "C",
                        "direct_majority": "D",
                        "strong_router_contract_count": 1,
                        "has_prompt_node_graph": True,
                        "predicted_answer": "C",
                    },
                ],
            }
        ]

        rows, summary = build_training_rows(records, min_score_margin=3)

        self.assertEqual(len(rows), 2)
        top = rows[0]
        other = rows[1]
        self.assertEqual(top["training_target"], "preferred_graph")
        self.assertEqual(other["training_target"], "non_preferred_graph")
        self.assertTrue(top["is_margin_top"])
        self.assertEqual(top["score_margin_to_next"], 4)
        self.assertEqual(summary["margin_top_tasks"], 1)
        self.assertFalse(DISALLOWED_FIELDS & set(top))
        self.assertFalse(DISALLOWED_FIELDS & set(other))

    def test_tied_top_variants_are_not_single_graph_training_targets(self):
        from experiment.aqua.graph_objective_training_export import build_training_rows

        records = [
            {
                "task_id": "task_tie",
                "slice_prefix": "synthetic",
                "ranked_variants": [
                    {"method_key": "router", "score": 9, "router_option": "A"},
                    {"method_key": "candidate", "score": 9, "router_option": "A"},
                    {"method_key": "calibrated", "score": 2, "router_option": "B"},
                ],
            }
        ]

        rows, summary = build_training_rows(records, min_score_margin=1)

        self.assertEqual(summary["top_score_ties"], 1)
        self.assertEqual(summary["margin_top_tasks"], 0)
        self.assertTrue(all(row["training_target"] == "multi_view_tie" for row in rows[:2]))
        self.assertEqual(rows[2]["training_target"], "non_preferred_graph")

    def test_real_first200_export_has_four_variants_per_task_and_no_gold_fields(self):
        from experiment.aqua.graph_objective_training_export import (
            build_training_rows,
            load_objective_records,
        )

        records = load_objective_records(
            "experiment/aqua/res_logs/aqua_first200_contract_graph_objective_summary.json"
        )
        rows, summary = build_training_rows(records, min_score_margin=3)

        self.assertEqual(summary["total_tasks"], 200)
        self.assertEqual(summary["variant_rows"], 800)
        self.assertEqual(summary["outcome_field_violations"], 0)
        self.assertEqual(len(rows), 800)
        self.assertGreater(summary["margin_top_tasks"], 0)
        self.assertTrue(all(not (DISALLOWED_FIELDS & set(row)) for row in rows))

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/graph_objective_training_export.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
