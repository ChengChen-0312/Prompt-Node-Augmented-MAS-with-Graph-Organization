import unittest


class MMLUTransferEvalReportTests(unittest.TestCase):
    def test_r162_report_summarizes_transfer_eval_without_overclaiming(self):
        from experiment.mmlu.transfer_eval_report import build_transfer_eval_summary

        summary = build_transfer_eval_summary()

        self.assertEqual(summary["rule"], "r162_mmlu_arg_transfer_eval")
        self.assertTrue(summary["transfer_result"])
        self.assertTrue(summary["same_model_as_argdesigner"])
        self.assertTrue(summary["checkpoint_loaded"])
        self.assertEqual(summary["llm_name"], "gpt-4o-2024-08-06")
        self.assertEqual(summary["dataset"], "mmlu")
        self.assertEqual(summary["total_tasks"], 100)
        self.assertEqual(summary["correct"], 88)
        self.assertAlmostEqual(summary["pass_at_1"], 0.88)
        self.assertAlmostEqual(summary["accuracy_percent"], 88.0)
        self.assertAlmostEqual(summary["cost"], 3.042140000000001)
        self.assertEqual(summary["prompt_tokens"], 301696)
        self.assertEqual(summary["completion_tokens"], 102244)
        self.assertEqual(summary["errors_detected"], [])
        self.assertFalse(summary["promptnode_result"])
        self.assertFalse(summary["aqua_accuracy_claim_supported"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_goal_audit_due"], "R165")

    def test_r162_report_records_weak_subjects_and_log_accuracy_display_boundary(self):
        from experiment.mmlu.transfer_eval_report import build_transfer_eval_summary

        summary = build_transfer_eval_summary()

        self.assertEqual(summary["weakest_subjects"][0]["subject"], "college_mathematics")
        self.assertEqual(summary["weakest_subjects"][0]["correct"], 7)
        self.assertEqual(summary["weakest_subjects"][0]["total"], 10)
        self.assertAlmostEqual(summary["weakest_subjects"][0]["accuracy_percent"], 70.0)
        self.assertEqual(summary["log_final_accuracy_display"], "0.88%")
        self.assertEqual(summary["log_final_accuracy_interpretation"], "display_bug_ratio_0.88_equals_88.0_percent")


if __name__ == "__main__":
    unittest.main()
