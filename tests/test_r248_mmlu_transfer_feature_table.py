import unittest

from experiment.mmlu.r248_mmlu_transfer_feature_table import (
    build_subject_stats,
    build_transfer_feature_row,
    summarize_transfer_rows,
)


class TestR248MMLUTransferFeatureTable(unittest.TestCase):
    def test_subject_stats_counts_accuracy(self):
        stats = build_subject_stats(
            [
                {"subject": "math", "is_correct": True},
                {"subject": "math", "is_correct": False},
            ]
        )

        self.assertEqual(stats["math"]["records"], 2)
        self.assertEqual(stats["math"]["correct"], 1)
        self.assertEqual(stats["math"]["error_rate"], 0.5)

    def test_feature_row_separates_features_and_labels(self):
        row = build_transfer_feature_row(
            {
                "task_id": "x",
                "subject": "math",
                "question": "Q\nOption A: 1\nOption B: 2",
                "predicted_answer": "A",
                "true_answer": "B",
                "is_correct": False,
            },
            {"math": {"records": 2, "correct": 1, "error_rate": 0.5, "accuracy": 0.5}},
            {"raw_contract_ready_rate": 0.04, "projected_contract_ready_rate": 1.0},
        )

        self.assertEqual(row["features"]["subject"], "math")
        self.assertEqual(row["labels"]["arg_error"], True)
        self.assertNotIn("true_answer", row["features"])

    def test_summary_counts_error_candidates(self):
        rows = [
            {"labels": {"arg_error": True}, "probe_priority": "arg_error_transfer_probe"},
            {"labels": {"arg_error": False}, "probe_priority": "control_correct_transfer_probe"},
        ]

        summary = summarize_transfer_rows(rows)

        self.assertEqual(summary["rows"], 2)
        self.assertEqual(summary["arg_errors"], 1)
        self.assertEqual(summary["probe_priorities"]["arg_error_transfer_probe"], 1)


if __name__ == "__main__":
    unittest.main()
