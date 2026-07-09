import unittest


class TestR305R306NonMathPromptNodes(unittest.TestCase):
    def test_nonmath_library_detects_statement_semantic_consistency(self):
        from experiment.mmlu.r305_nonmath_promptnode_library import propose_nonmath_candidate

        row = {
            "task_id": "not-used",
            "question": "Statement 1| In a Bayesian network, the inference results of the junction tree algorithm are the same as the inference results of variable elimination. Statement 2| If two random variable X and Y are conditionally independent given another random variable Z, then in the corresponding Bayesian network, the nodes for X and Y are d-separated given Z.\nOption A: True, True\nOption B: False, False\nOption C: True, False\nOption D: False, True",
            "predicted_answer": "A",
        }

        candidate = propose_nonmath_candidate(row)

        self.assertEqual(candidate["candidate_type"], "option_semantic_consistency")
        self.assertEqual(candidate["candidate_label"], "C")
        self.assertIn("PN_OptionSemanticConsistency", candidate["promptnode_roles"])

    def test_nonmath_library_detects_all_of_these_conceptual_consistency(self):
        from experiment.mmlu.r305_nonmath_promptnode_library import propose_nonmath_candidate

        row = {
            "task_id": "not-used",
            "question": "Bow waves are produced by waves of water\nOption A: overlapping one another\nOption B: constructively interfering\nOption C: moving slower than the source producing them\nOption D: All of these",
            "predicted_answer": "B",
        }

        candidate = propose_nonmath_candidate(row)

        self.assertEqual(candidate["candidate_type"], "conceptual_all_of_these_consistency")
        self.assertEqual(candidate["candidate_label"], "D")

    def test_nonmath_library_flags_truncated_input_for_memory_bridge(self):
        from experiment.mmlu.r305_nonmath_promptnode_library import propose_nonmath_candidate

        row = {
            "task_id": "truncated",
            "question": "A baseball team sold 215 youth tickets for $3 ea\nOption A: (215 × 3) – (467 × 7)",
            "predicted_answer": "A",
        }

        candidate = propose_nonmath_candidate(row)

        self.assertEqual(candidate["candidate_type"], "memory_bridge_required")
        self.assertEqual(candidate["candidate_label"], "")
        self.assertIn("PN_MemoryBridge", candidate["promptnode_roles"])

    def test_r306_stack_reports_gain_without_using_excluded_tasks(self):
        from experiment.mmlu.r306_nonmath_stack_eval import apply_nonmath_stack, summarize_nonmath_records

        rows = [
            {
                "task_id": "MMLU-high_school_statistics_test-32",
                "audit_excluded": True,
                "question": "Statement 1| x\nOption C: True, False",
                "arg_prediction": "A",
                "predicted_answer": "A",
                "true_answer": "C",
                "audit_clean_answer": "C",
                "is_correct": False,
                "audit_clean_is_correct": False,
            },
            {
                "task_id": "ml",
                "audit_excluded": False,
                "question": "Statement 1| In a Bayesian network, the inference results of the junction tree algorithm are the same as the inference results of variable elimination. Statement 2| If two random variable X and Y are conditionally independent given another random variable Z, then in the corresponding Bayesian network, the nodes for X and Y are d-separated given Z.\nOption A: True, True\nOption C: True, False",
                "arg_prediction": "A",
                "predicted_answer": "A",
                "true_answer": "C",
                "audit_clean_answer": "C",
                "is_correct": False,
                "audit_clean_is_correct": False,
            },
        ]

        records = [apply_nonmath_stack(row) for row in rows]
        summary = summarize_nonmath_records(records, r304_main_correct=0, r304_main_audit_clean_correct=0)

        self.assertEqual(summary["main_records"], 1)
        self.assertEqual(summary["main_correct"], 1)
        self.assertEqual(summary["main_fix_harm"], "1/0")
        self.assertEqual(summary["appendix_excluded_records"], 1)


if __name__ == "__main__":
    unittest.main()
