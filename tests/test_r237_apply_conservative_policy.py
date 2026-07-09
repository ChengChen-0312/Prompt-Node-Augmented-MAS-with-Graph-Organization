import unittest

from experiment.mmlu.r237_apply_conservative_policy import (
    apply_policy_to_manifest_row,
    summarize_policy_application,
)


class TestR237ApplyConservativePolicy(unittest.TestCase):
    def _row(self, task_id="task_1", majority_count=1):
        return {
            "task_id": task_id,
            "split_role": "train",
            "model_visible_input": {
                "baseline_prediction": "A",
                "objective_prediction": "B",
                "objective_prediction_differs_from_baseline": True,
                "objective_top_score": 3,
                "baseline_direct_majority_count": majority_count,
            },
        }

    def test_policy_switches_and_fixes_when_guard_allows(self):
        source = {"task_1": {"true_answer": "B"}}

        output = apply_policy_to_manifest_row(
            self._row(majority_count=1),
            source,
            "baseline_consensus_guard_top3",
        )

        self.assertTrue(output["switch"])
        self.assertEqual(output["selected_prediction"], "B")
        self.assertTrue(output["fix"])

    def test_policy_abstains_when_baseline_majority_is_strong(self):
        source = {"task_1": {"true_answer": "A"}}

        output = apply_policy_to_manifest_row(
            self._row(majority_count=3),
            source,
            "baseline_consensus_guard_top3",
        )

        self.assertFalse(output["switch"])
        self.assertEqual(output["selected_prediction"], "A")
        self.assertFalse(output["harm"])

    def test_summary_counts_split_metrics(self):
        source = {
            "task_1": {"true_answer": "B"},
            "task_2": {"true_answer": "A"},
        }
        outputs = [
            apply_policy_to_manifest_row(self._row("task_1", majority_count=1), source, "baseline_consensus_guard_top3"),
            apply_policy_to_manifest_row(self._row("task_2", majority_count=3), source, "baseline_consensus_guard_top3"),
        ]

        summary = summarize_policy_application(outputs)

        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["accuracy_count"], 2)
        self.assertEqual(summary["fixes"], 1)
        self.assertEqual(summary["harms"], 0)


if __name__ == "__main__":
    unittest.main()
