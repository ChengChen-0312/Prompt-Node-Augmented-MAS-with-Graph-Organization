import unittest


class TestR364SourceInvariantFreshEvalAnalysis(unittest.TestCase):
    def test_analysis_records_positive_delta_no_harm_and_wrong_forward(self):
        from experiment.mmlu.r364_source_invariant_fresh_eval_analysis import build_fresh_eval_analysis

        summary = build_fresh_eval_analysis()

        self.assertEqual(summary["run_id"], "R364")
        self.assertEqual(summary["records"], 48)
        self.assertEqual(summary["arg_correct"], 36)
        self.assertEqual(summary["hybrid_correct"], 37)
        self.assertEqual(summary["delta_correct"], 1)
        self.assertEqual(summary["fixes"], 1)
        self.assertEqual(summary["harms"], 0)
        self.assertEqual(summary["gate_forward_count"], 8)
        self.assertEqual(summary["wrong_forward_count"], 1)
        self.assertTrue(summary["claim_permissions"]["fresh_positive_delta_no_harm_claim_allowed"])
        self.assertFalse(summary["claim_permissions"]["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R365_wrong_forward_and_missed_fix_analysis")


if __name__ == "__main__":
    unittest.main()
