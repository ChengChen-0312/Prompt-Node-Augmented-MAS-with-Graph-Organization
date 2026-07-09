import unittest

from experiment.mmlu.r251_mmlu_probe_selection import (
    build_balanced_probe_rows,
    select_subject_matched_controls,
    summarize_probe_rows,
)


class TestR251MMLUProbeSelection(unittest.TestCase):
    def test_subject_matched_controls_use_same_subjects(self):
        errors = [
            {"task_id": "e1", "features": {"subject": "math"}, "labels": {"arg_error": True}},
            {"task_id": "e2", "features": {"subject": "physics"}, "labels": {"arg_error": True}},
        ]
        controls = [
            {"task_id": "c1", "features": {"subject": "math"}, "labels": {"arg_error": False}},
            {"task_id": "c2", "features": {"subject": "physics"}, "labels": {"arg_error": False}},
        ]

        selected = select_subject_matched_controls(errors, controls)

        self.assertEqual([row["task_id"] for row in selected], ["c1", "c2"])

    def test_balanced_rows_mark_probe_roles(self):
        feature_rows = [
            {"task_id": "e1", "features": {"subject": "math"}, "labels": {"arg_error": True}},
            {"task_id": "c1", "features": {"subject": "math"}, "labels": {"arg_error": False}},
        ]

        rows = build_balanced_probe_rows(feature_rows)

        self.assertEqual(len(rows), 2)
        self.assertEqual({row["selection_role"] for row in rows}, {"arg_error", "matched_control"})

    def test_summary_reports_balance(self):
        summary = summarize_probe_rows(
            [
                {"selection_role": "arg_error", "features": {"subject": "math"}},
                {"selection_role": "matched_control", "features": {"subject": "math"}},
            ]
        )

        self.assertEqual(summary["rows"], 2)
        self.assertEqual(summary["role_counts"]["arg_error"], 1)
        self.assertTrue(summary["balanced_error_control"])


if __name__ == "__main__":
    unittest.main()
