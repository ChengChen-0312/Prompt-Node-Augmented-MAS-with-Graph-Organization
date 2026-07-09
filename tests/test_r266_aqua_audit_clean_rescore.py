import unittest

from experiment.aqua.r266_aqua_audit_clean_rescore import (
    audit_task114_literal_formula,
    build_rescore_summary,
    score_rows,
)


class TestR266AquaAuditCleanRescore(unittest.TestCase):
    def test_score_rows_excludes_bad_tasks_and_applies_corrections(self):
        rows = [
            {"task_id": "task_1", "true_answer": "A", "predicted_answer": "A"},
            {"task_id": "task_59", "true_answer": "C", "predicted_answer": "D"},
            {"task_id": "task_114", "true_answer": "D", "predicted_answer": "C"},
        ]

        filtered = score_rows(rows, excluded_task_ids={"task_59"}, corrected_labels={})
        corrected = score_rows(rows, excluded_task_ids={"task_59"}, corrected_labels={"task_114": "C"})

        self.assertEqual(filtered["accuracy"], "1/2")
        self.assertEqual(corrected["accuracy"], "2/2")
        self.assertEqual(corrected["rows"][1]["effective_answer"], "C")

    def test_task114_literal_formula_flags_official_boundary_error(self):
        audit = audit_task114_literal_formula()

        self.assertEqual(audit["official_label"], "D")
        self.assertEqual(audit["deterministic_label"], "C")
        self.assertFalse(audit["official_label_supported_strict"])
        self.assertEqual(audit["error_category"], "official_label_boundary_error")

    def test_summary_reports_filtered_and_task114_sensitive_scores(self):
        arg_rows = [
            {"task_id": "task_59", "true_answer": "C", "predicted_answer": "B"},
            {"task_id": "task_114", "true_answer": "D", "predicted_answer": "C"},
            {"task_id": "task_250", "true_answer": "E", "predicted_answer": "A"},
        ]
        r065_rows = [
            {"task_id": "task_59", "true_answer": "C", "predicted_answer": "D"},
            {"task_id": "task_114", "true_answer": "D", "predicted_answer": "D"},
            {"task_id": "task_250", "true_answer": "E", "predicted_answer": "E"},
        ]
        summary = build_rescore_summary(arg_rows, r065_rows)

        self.assertEqual(summary["scenarios"]["exclude_59_139_228"]["R065"]["accuracy"], "2/2")
        self.assertEqual(summary["scenarios"]["exclude_59_139_228_correct_114"]["ARG"]["accuracy"], "1/2")
        self.assertEqual(summary["scenarios"]["exclude_59_139_228_correct_114"]["R065"]["accuracy"], "1/2")


if __name__ == "__main__":
    unittest.main()
