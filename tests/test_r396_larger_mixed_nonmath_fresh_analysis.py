import unittest


class TestR396LargerMixedNonmathFreshAnalysis(unittest.TestCase):
    def test_analysis_records_no_harm_but_no_positive_gain_and_goal_audit(self):
        from experiment.mmlu.r396_larger_mixed_nonmath_fresh_analysis import build_larger_mixed_analysis

        summary = build_larger_mixed_analysis()

        self.assertEqual(summary["run_id"], "R396")
        self.assertEqual(summary["records"], 48)
        self.assertEqual(summary["arg_correct"], 41)
        self.assertEqual(summary["hybrid_correct"], 41)
        self.assertEqual(summary["delta_correct"], 0)
        self.assertEqual(summary["fixes"], 0)
        self.assertEqual(summary["harms"], 0)
        self.assertEqual(summary["wrong_forward_count"], 3)
        self.assertEqual(summary["missed_fix_count"], 4)
        self.assertEqual(summary["candidate_correct_but_blocked_count"], 1)
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R391", "R392", "R393", "R394", "R395"])
        self.assertTrue(summary["goal_alignment"]["larger_mixed_no_harm"])
        self.assertFalse(summary["goal_alignment"]["larger_mixed_positive"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R397_larger_mixed_error_taxonomy")


if __name__ == "__main__":
    unittest.main()
