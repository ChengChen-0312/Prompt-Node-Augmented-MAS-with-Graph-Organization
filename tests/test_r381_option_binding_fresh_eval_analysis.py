import unittest


class TestR381OptionBindingFreshEvalAnalysis(unittest.TestCase):
    def test_analysis_flags_positive_delta_and_plain_requery_control_need(self):
        from experiment.mmlu.r381_option_binding_fresh_eval_analysis import build_option_binding_fresh_analysis

        summary = build_option_binding_fresh_analysis()

        self.assertEqual(summary["run_id"], "R381")
        self.assertEqual(summary["records"], 24)
        self.assertEqual(summary["arg_correct"], 21)
        self.assertEqual(summary["hybrid_correct"], 24)
        self.assertEqual(summary["delta_correct"], 3)
        self.assertEqual(summary["fixes"], 3)
        self.assertEqual(summary["harms"], 0)
        self.assertEqual(summary["wrong_forward_count"], 0)
        self.assertEqual(summary["gate_forward_count"], 24)
        self.assertTrue(summary["claim_permissions"]["fresh_positive_delta_no_harm_claim_allowed"])
        self.assertTrue(summary["claim_risks"]["plain_requery_control_required"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R382_plain_requery_control_preflight")


if __name__ == "__main__":
    unittest.main()
