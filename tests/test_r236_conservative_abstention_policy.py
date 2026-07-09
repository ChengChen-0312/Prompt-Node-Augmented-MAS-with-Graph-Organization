import unittest

from experiment.mmlu.r236_conservative_abstention_policy import (
    evaluate_policy,
    policy_switches,
)


class TestR236ConservativeAbstentionPolicy(unittest.TestCase):
    def _feature(self, score=3, baseline="A", objective="B", majority_count=1):
        return {
            "baseline_prediction": baseline,
            "objective_prediction": objective,
            "objective_prediction_differs_from_baseline": baseline != objective,
            "objective_top_score": score,
            "baseline_direct_majority_count": majority_count,
        }

    def test_current_top3_switches_on_score_three(self):
        self.assertTrue(policy_switches("current_top3", self._feature(score=3)))

    def test_consensus_guard_abstains_on_strong_baseline_majority(self):
        self.assertFalse(
            policy_switches("baseline_consensus_guard_top3", self._feature(score=3, majority_count=3))
        )

    def test_consensus_guard_switches_when_baseline_not_strong(self):
        self.assertTrue(
            policy_switches("baseline_consensus_guard_top3", self._feature(score=3, majority_count=1))
        )

    def test_high_confidence_top10_requires_score_ten(self):
        self.assertFalse(policy_switches("high_confidence_top10", self._feature(score=9)))
        self.assertTrue(policy_switches("high_confidence_top10", self._feature(score=10)))

    def test_evaluate_policy_counts_fix_and_harm(self):
        rows = [
            {"task_id": "a", "true_answer": "B", "baseline_prediction": "A"},
            {"task_id": "b", "true_answer": "A", "baseline_prediction": "A"},
        ]
        features = {
            "a": self._feature(score=3, baseline="A", objective="B", majority_count=1),
            "b": self._feature(score=3, baseline="A", objective="B", majority_count=3),
        }

        result = evaluate_policy(rows, features, "baseline_consensus_guard_top3")

        self.assertEqual(result["accuracy_count"], 2)
        self.assertEqual(result["fixes"], 1)
        self.assertEqual(result["harms"], 0)
        self.assertEqual(result["switches"], 1)


if __name__ == "__main__":
    unittest.main()
