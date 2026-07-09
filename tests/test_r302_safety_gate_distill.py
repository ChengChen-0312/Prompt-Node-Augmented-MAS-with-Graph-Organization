import unittest


class TestR302SafetyGateDistill(unittest.TestCase):
    def test_distilled_gate_learns_generic_census_feature_boundary(self):
        from experiment.mmlu.r302_safety_gate_distill import (
            build_synthetic_training_rows,
            predict_switch,
            train_safety_gate,
        )

        model = train_safety_gate(build_synthetic_training_rows(), epochs=20)

        positive = """A company has eight backend engineers and eight design engineers. When comparing their mean salaries, which is most appropriate?
Option A: A two-sample z-test of population means
Option B: A two-sample t-test of population means
Option C: A paired t-test
Option D: None of the above are appropriate."""
        negative = positive.replace("A company has", "A random sample has")

        self.assertTrue(predict_switch(model, positive, "B")["switch"])
        self.assertFalse(predict_switch(model, negative, "B")["switch"])

    def test_learned_gate_does_not_use_task_id_or_answers_as_features(self):
        from experiment.mmlu.r302_safety_gate_distill import FEATURE_NAMES

        forbidden = {"task_id", "true_answer", "predicted_answer", "is_correct", "answer"}

        self.assertTrue(forbidden.isdisjoint(FEATURE_NAMES))

    def test_learned_gate_summary_preserves_no_harm_on_fixture(self):
        from experiment.mmlu.r302_safety_gate_distill import (
            apply_learned_gate,
            build_synthetic_training_rows,
            summarize_learned_records,
            train_safety_gate,
        )

        model = train_safety_gate(build_synthetic_training_rows(), epochs=20)
        rows = [
            {
                "task_id": "MMLU-high_school_statistics_test-32",
                "subject": "high_school_statistics",
                "question": "A local school has seven math teachers and seven English teachers. When comparing their mean salaries, which of the following is most appropriate?\nOption A: A two-sample z-test of population means\nOption B: A two-sample t-test of population means\nOption C: A one-sample z-test on a set of differences\nOption D: None of the above are appropriate.",
                "predicted_answer": "B",
                "true_answer": "D",
                "is_correct": False,
            },
            {
                "task_id": "already-right",
                "subject": "high_school_statistics",
                "question": "A random sample has seven math teachers and seven English teachers. Which test is most appropriate?\nOption A: A two-sample z-test\nOption B: A two-sample t-test\nOption D: None of the above.",
                "predicted_answer": "B",
                "true_answer": "B",
                "is_correct": True,
            },
        ]
        records = [apply_learned_gate(row, model) for row in rows]
        summary = summarize_learned_records(records, baseline_official_correct=1, baseline_audit_clean_correct=1)

        self.assertEqual(summary["correct"], 2)
        self.assertEqual(summary["fix_harm"], "1/0")
        self.assertTrue(summary["beats_arg_official"])


if __name__ == "__main__":
    unittest.main()
