import unittest

from experiment.mmlu.r242_fit_abstention_policy import (
    evaluate_policy_spec,
    fit_policy_spec,
    policy_spec_switches,
)


class TestR242FitAbstentionPolicy(unittest.TestCase):
    def _row(self, score, majority_count, true_answer, baseline="A", objective="B", split="train"):
        return {
            "task_id": f"{score}-{majority_count}-{true_answer}",
            "split_role": split,
            "baseline_prediction": baseline,
            "objective_prediction": objective,
            "true_answer": true_answer,
            "features": {
                "objective_differs": baseline != objective,
                "objective_top_score": score,
                "baseline_direct_majority_count": majority_count,
            },
            "labels": {
                "baseline_correct": baseline == true_answer,
                "objective_correct": objective == true_answer,
                "beneficial_switch": baseline != true_answer and objective == true_answer,
                "harmful_switch": baseline == true_answer and objective != true_answer,
            },
        }

    def test_policy_spec_switches_by_threshold_and_majority_guard(self):
        spec = {"score_threshold": 3, "majority_count_lt": 3}

        self.assertTrue(policy_spec_switches(spec, self._row(3, 2, "B")["features"]))
        self.assertFalse(policy_spec_switches(spec, self._row(3, 3, "B")["features"]))
        self.assertFalse(policy_spec_switches(spec, self._row(2, 1, "B")["features"]))

    def test_evaluate_policy_spec_counts_fix_and_harm(self):
        spec = {"score_threshold": 3, "majority_count_lt": 3}
        rows = [
            self._row(3, 1, "B"),
            self._row(3, 3, "A"),
        ]

        result = evaluate_policy_spec(spec, rows)

        self.assertEqual(result["accuracy_count"], 2)
        self.assertEqual(result["fixes"], 1)
        self.assertEqual(result["harms"], 0)

    def test_fit_policy_prefers_more_switch_coverage_when_train_metrics_tie(self):
        rows = [
            self._row(3, 2, "B"),
            self._row(5, 1, "B"),
            self._row(3, 3, "A"),
        ]

        fitted = fit_policy_spec(rows)

        self.assertEqual(fitted["spec"]["score_threshold"], 3)
        self.assertEqual(fitted["spec"]["majority_count_lt"], 3)


if __name__ == "__main__":
    unittest.main()
