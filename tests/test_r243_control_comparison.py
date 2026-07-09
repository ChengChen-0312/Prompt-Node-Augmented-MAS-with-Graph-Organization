import unittest

from experiment.mmlu.r243_control_comparison import (
    evaluate_variant_records,
)


class TestR243ControlComparison(unittest.TestCase):
    def test_evaluate_variant_records_counts_fix_harm(self):
        rows = [
            {
                "task_id": "a",
                "router_action": "switch_to_objective",
                "target_option_label": "B",
                "model_visible_input": {"baseline_prediction": "A"},
            },
            {
                "task_id": "b",
                "router_action": "abstain",
                "target_option_label": "NONE",
                "model_visible_input": {"baseline_prediction": "A"},
            },
        ]
        source = {"a": {"true_answer": "B"}, "b": {"true_answer": "A"}}

        result = evaluate_variant_records(rows, source)

        self.assertEqual(result["records"], 2)
        self.assertEqual(result["accuracy_count"], 2)
        self.assertEqual(result["fixes"], 1)
        self.assertEqual(result["harms"], 0)


if __name__ == "__main__":
    unittest.main()
