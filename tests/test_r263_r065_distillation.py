import unittest

from experiment.aqua.r263_r065_distillation import (
    evaluate_gate,
    gate_triggers,
    search_gate_specs,
)


class TestR263R065Distillation(unittest.TestCase):
    def test_gate_triggers_from_risk_and_top_score(self):
        features = {"risk_score": 2, "objective_top_score": 2, "objective_differs_from_arg": True}

        self.assertTrue(
            gate_triggers(
                features,
                {"name": "risk_ge_1_top_ge_2", "risk_min": 1, "objective_top_score_min": 2},
            )
        )

    def test_evaluate_gate_counts_trigger_cost_and_fix_harm(self):
        rows = [
            {
                "task_id": "a",
                "arg_correct": False,
                "teacher_correct": True,
                "teacher_would_fix": True,
                "teacher_would_harm": False,
                "features": {"risk_score": 2, "objective_top_score": 2},
                "labels_not_model_visible": {"clean_label": "clean"},
            },
            {
                "task_id": "b",
                "arg_correct": True,
                "teacher_correct": True,
                "teacher_would_fix": False,
                "teacher_would_harm": False,
                "features": {"risk_score": 0, "objective_top_score": 0},
                "labels_not_model_visible": {"clean_label": "clean"},
            },
        ]
        result = evaluate_gate(rows, {"name": "risk_ge_1", "risk_min": 1}, promptnode_cost_per_trigger=0.1)

        self.assertEqual(result["selected_correct"], 2)
        self.assertEqual(result["triggers"], 1)
        self.assertEqual(result["fixes"], 1)
        self.assertEqual(result["harms"], 0)
        self.assertEqual(result["estimated_incremental_cost"], 0.1)

    def test_search_returns_sorted_candidates(self):
        rows = [
            {
                "arg_correct": False,
                "teacher_correct": True,
                "teacher_would_fix": True,
                "teacher_would_harm": False,
                "features": {"risk_score": 2, "objective_top_score": 2, "objective_differs_from_arg": True},
                "labels_not_model_visible": {"clean_label": "clean"},
            },
            {
                "arg_correct": True,
                "teacher_correct": True,
                "teacher_would_fix": False,
                "teacher_would_harm": False,
                "features": {"risk_score": 0, "objective_top_score": 0, "objective_differs_from_arg": False},
                "labels_not_model_visible": {"clean_label": "clean"},
            },
        ]
        candidates = search_gate_specs(rows, promptnode_cost_per_trigger=0.1)

        self.assertEqual(candidates[0]["harms"], 0)
        self.assertGreaterEqual(candidates[0]["selected_correct"], 2)


if __name__ == "__main__":
    unittest.main()
