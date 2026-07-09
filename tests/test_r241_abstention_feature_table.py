import unittest

from experiment.mmlu.r241_abstention_feature_table import (
    build_feature_row,
    summarize_feature_rows,
)


class TestR241AbstentionFeatureTable(unittest.TestCase):
    def _manifest_row(self):
        return {
            "task_id": "task_1",
            "split_role": "train",
            "training_allowed": True,
            "frozen_eval_only": False,
            "model_visible_input": {
                "baseline_prediction": "A",
                "objective_prediction": "B",
                "objective_prediction_differs_from_baseline": True,
                "objective_top_score": 3,
                "baseline_direct_majority": "A",
                "baseline_direct_majority_count": 2,
                "baseline_direct_valid_vote_count": 3,
                "baseline_direct_votes_split": True,
            },
        }

    def test_build_feature_row_marks_beneficial_switch(self):
        row = build_feature_row(self._manifest_row(), {"true_answer": "B", "clean_label": "clean"})

        self.assertTrue(row["features"]["objective_differs"])
        self.assertEqual(row["features"]["objective_top_score"], 3)
        self.assertTrue(row["labels"]["beneficial_switch"])
        self.assertFalse(row["labels"]["harmful_switch"])

    def test_build_feature_row_marks_harmful_switch(self):
        row = build_feature_row(self._manifest_row(), {"true_answer": "A", "clean_label": "clean"})

        self.assertFalse(row["labels"]["beneficial_switch"])
        self.assertTrue(row["labels"]["harmful_switch"])
        self.assertTrue(row["labels"]["clean_harm_if_switch"])

    def test_summary_counts_train_and_frozen_labels(self):
        train = build_feature_row(self._manifest_row(), {"true_answer": "B", "clean_label": "clean"})
        frozen_manifest = self._manifest_row()
        frozen_manifest["split_role"] = "frozen_eval"
        frozen_manifest["training_allowed"] = False
        frozen_manifest["frozen_eval_only"] = True
        frozen = build_feature_row(frozen_manifest, {"true_answer": "A", "clean_label": "clean"})

        summary = summarize_feature_rows([train, frozen])

        self.assertEqual(summary["rows"], 2)
        self.assertEqual(summary["train_rows"], 1)
        self.assertEqual(summary["frozen_eval_rows"], 1)
        self.assertEqual(summary["beneficial_switch_labels"], 1)
        self.assertEqual(summary["harmful_switch_labels"], 1)


if __name__ == "__main__":
    unittest.main()
