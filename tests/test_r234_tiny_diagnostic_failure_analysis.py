import unittest

from experiment.mmlu.r234_tiny_diagnostic_failure_analysis import (
    classify_task_outcome,
    summarize_failure_modes,
)


class TestR234TinyDiagnosticFailureAnalysis(unittest.TestCase):
    def _rows(self, true_answer="D", baseline="NONE", objective="D", proposed="D", abstain="NONE"):
        return [
            {
                "task_id": "task_1",
                "control_variant": "proposed_router_final",
                "true_answer": true_answer,
                "baseline_prediction": baseline,
                "objective_prediction": objective,
                "predicted_answer": proposed,
                "is_correct": proposed == true_answer,
                "fix": baseline != true_answer and proposed == true_answer,
                "harm": baseline == true_answer and proposed != true_answer,
            },
            {
                "task_id": "task_1",
                "control_variant": "abstain_only_router",
                "true_answer": true_answer,
                "baseline_prediction": baseline,
                "objective_prediction": objective,
                "predicted_answer": abstain,
                "is_correct": abstain == true_answer,
            },
            {
                "task_id": "task_1",
                "control_variant": "always_switch_to_objective",
                "true_answer": true_answer,
                "baseline_prediction": baseline,
                "objective_prediction": objective,
                "predicted_answer": objective,
                "is_correct": objective == true_answer,
            },
        ]

    def test_classifies_objective_fix_when_baseline_wrong(self):
        outcome = classify_task_outcome(self._rows())

        self.assertEqual(outcome["failure_mode"], "objective_correct_router_followed")
        self.assertTrue(outcome["proposed_fix"])

    def test_classifies_objective_harm_when_baseline_correct(self):
        outcome = classify_task_outcome(
            self._rows(true_answer="A", baseline="A", objective="B", proposed="B", abstain="A")
        )

        self.assertEqual(outcome["failure_mode"], "objective_wrong_router_harmed_baseline")
        self.assertTrue(outcome["proposed_harm"])

    def test_classifies_no_available_fix_when_baseline_and_objective_wrong(self):
        outcome = classify_task_outcome(
            self._rows(true_answer="E", baseline="C", objective="A", proposed="A", abstain="C")
        )

        self.assertEqual(outcome["failure_mode"], "baseline_and_objective_wrong")

    def test_summary_counts_failure_modes(self):
        outcomes = [
            {"failure_mode": "objective_correct_router_followed", "proposed_fix": True, "proposed_harm": False},
            {"failure_mode": "objective_wrong_router_harmed_baseline", "proposed_fix": False, "proposed_harm": True},
        ]

        summary = summarize_failure_modes(outcomes)

        self.assertEqual(summary["tasks"], 2)
        self.assertEqual(summary["failure_modes"]["objective_correct_router_followed"], 1)
        self.assertEqual(summary["proposed_fixes"], 1)
        self.assertEqual(summary["proposed_harms"], 1)


if __name__ == "__main__":
    unittest.main()
