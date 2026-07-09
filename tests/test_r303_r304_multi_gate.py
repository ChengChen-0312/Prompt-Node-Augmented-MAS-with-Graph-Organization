import unittest


class TestR303R304MultiGate(unittest.TestCase):
    def test_r303_excludes_three_audited_tasks_from_main_training_protocol(self):
        from experiment.mmlu.r303_audit_exclusion_protocol import build_exclusion_summary

        summary = build_exclusion_summary()

        self.assertEqual(summary["run_id"], "R303")
        self.assertEqual(summary["excluded_count"], 3)
        self.assertIn("MMLU-high_school_statistics_test-32", summary["excluded_task_ids"])
        self.assertEqual(summary["main_eval_records"], 97)
        self.assertEqual(summary["arg_main_official_correct"], 88)
        self.assertEqual(summary["arg_main_audit_clean_correct"], 88)

    def test_symbolic_verifiers_fix_non_excluded_mmlu_errors_without_task_id(self):
        from experiment.mmlu.r304_multi_trigger_safety_gate import propose_virtual_node_candidate

        expression = {
            "task_id": "not-used",
            "question": "A baseball team sold 215 youth tickets for $3 each and 467 adult tickets for $7 each. Which expression can be used to find how much more money the baseball team made on adult tickets than on youth tickets?\nOption A: (215 × 3) – (467 × 7)\nOption B: (215 × 7) – (467 × 3)\nOption C: (467 × 3) – (215 × 7)\nOption D: (467 × 7) – (215 × 3)",
            "predicted_answer": "A",
        }
        ev = {
            "task_id": "not-used",
            "question": "Two dice are rolled simultaneously. If both dice show 6, then the player wins $20; otherwise the player loses the game. It costs $2.00 to play the game. What is the expected gain or loss per game?\nOption A: The player will gain about $0.55.\nOption B: The player will gain about $1.44.\nOption C: The player will lose about $0.55.\nOption D: The player will lose about $1.44.",
            "predicted_answer": "C",
        }

        self.assertEqual(propose_virtual_node_candidate(expression)["candidate_label"], "D")
        self.assertEqual(propose_virtual_node_candidate(ev)["candidate_label"], "D")

    def test_learned_multi_gate_reports_main97_gain_excluding_audit_items(self):
        from experiment.mmlu.r304_multi_trigger_safety_gate import (
            apply_multi_gate,
            build_synthetic_training_rows,
            summarize_records,
            train_forward_gate,
        )

        model = train_forward_gate(build_synthetic_training_rows(), epochs=25)
        rows = [
            {
                "task_id": "MMLU-high_school_statistics_test-32",
                "subject": "high_school_statistics",
                "question": "A local school has seven math teachers and seven English teachers. When comparing their mean salaries, which of the following is most appropriate?\nOption A: A two-sample z-test\nOption B: A two-sample t-test\nOption D: None of the above are appropriate.",
                "predicted_answer": "B",
                "true_answer": "D",
                "is_correct": False,
            },
            {
                "task_id": "money-expression",
                "subject": "elementary_mathematics",
                "question": "A baseball team sold 215 youth tickets for $3 each and 467 adult tickets for $7 each. Which expression can be used to find how much more money the baseball team made on adult tickets than on youth tickets?\nOption A: (215 × 3) – (467 × 7)\nOption D: (467 × 7) – (215 × 3)",
                "predicted_answer": "A",
                "true_answer": "D",
                "is_correct": False,
            },
        ]
        records = [apply_multi_gate(row, model) for row in rows]
        summary = summarize_records(records, baseline_official_correct=0, baseline_audit_clean_correct=0)

        self.assertEqual(summary["main_records"], 1)
        self.assertEqual(summary["main_correct"], 1)
        self.assertEqual(summary["main_fix_harm"], "1/0")
        self.assertEqual(summary["appendix_excluded_records"], 1)
        self.assertTrue(summary["beats_arg_main_official"])


if __name__ == "__main__":
    unittest.main()
