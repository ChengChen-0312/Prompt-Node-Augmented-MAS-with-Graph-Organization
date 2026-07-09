import unittest


STATS_CENSUS_QUESTION = """A local school has seven math teachers and seven English teachers. When comparing their mean salaries, which of the following is most appropriate?
Option A: A two-sample z-test of population means
Option B: A two-sample t-test of population means
Option C: A one-sample z-test on a set of differences
Option D: None of the above are appropriate."""


class TestR300R301MmluAuditGate(unittest.TestCase):
    def test_r300_audit_marks_redux_wrong_groundtruth_items(self):
        from experiment.mmlu.r300_goal_and_label_audit import build_label_audit_summary

        summary = build_label_audit_summary()

        self.assertEqual(summary["run_id"], "R300")
        self.assertEqual(summary["audit_clean_overrides"]["MMLU-high_school_physics_test-67"], "C")
        self.assertEqual(summary["audit_clean_overrides"]["MMLU-college_chemistry_test-62"], "A")
        self.assertGreaterEqual(summary["wrong_groundtruth_count"], 2)
        self.assertEqual(summary["arg_r162_official_correct"], 88)
        self.assertEqual(summary["arg_r162_audit_clean_correct"], 90)

    def test_census_gate_switches_complete_population_inference_item_to_none(self):
        from experiment.mmlu.r301_conservative_census_gate import apply_census_gate

        row = {
            "task_id": "stats-census",
            "subject": "high_school_statistics",
            "question": STATS_CENSUS_QUESTION,
            "arg_prediction": "B",
            "true_answer": "D",
        }

        selected = apply_census_gate(row)

        self.assertEqual(selected["predicted_answer"], "D")
        self.assertEqual(selected["decision_rule"], "switch_census_no_inference_mismatch")
        self.assertEqual(selected["lifecycle_actions"], ["write", "forward", "upgrade"])
        self.assertTrue(selected["model_visible_features_only"])

    def test_census_gate_does_not_switch_when_question_says_sample(self):
        from experiment.mmlu.r301_conservative_census_gate import apply_census_gate

        sample_question = STATS_CENSUS_QUESTION.replace(
            "A local school has seven math teachers and seven English teachers.",
            "A random sample has seven math teachers and seven English teachers.",
        )
        row = {
            "task_id": "stats-sample",
            "subject": "high_school_statistics",
            "question": sample_question,
            "arg_prediction": "B",
            "true_answer": "D",
        }

        selected = apply_census_gate(row)

        self.assertEqual(selected["predicted_answer"], "B")
        self.assertEqual(selected["decision_rule"], "keep_arg_no_gate_trigger")
        self.assertIn("prune", selected["lifecycle_actions"])

    def test_r301_summary_reports_official_and_audit_clean_gain(self):
        from experiment.mmlu.r301_conservative_census_gate import build_gate_records, summarize_gate_records

        rows = [
            {
                "task_id": "MMLU-high_school_statistics_test-32",
                "subject": "high_school_statistics",
                "question": STATS_CENSUS_QUESTION,
                "predicted_answer": "B",
                "true_answer": "D",
                "is_correct": False,
            },
            {
                "task_id": "MMLU-high_school_physics_test-67",
                "subject": "high_school_physics",
                "question": "Which circuit change always increases current?\nOption A: Increased voltage and increased resistance\nOption C: Increased voltage and decreased resistance",
                "predicted_answer": "C",
                "true_answer": "A",
                "is_correct": False,
            },
        ]

        records = build_gate_records(rows)
        summary = summarize_gate_records(records, baseline_official_correct=0, baseline_audit_clean_correct=1)

        self.assertEqual(summary["correct"], 1)
        self.assertEqual(summary["audit_clean_correct"], 2)
        self.assertEqual(summary["fixes"], 1)
        self.assertEqual(summary["harms"], 0)
        self.assertTrue(summary["beats_arg_official"])
        self.assertTrue(summary["beats_arg_audit_clean"])


if __name__ == "__main__":
    unittest.main()
