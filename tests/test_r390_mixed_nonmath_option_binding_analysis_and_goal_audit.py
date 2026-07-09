import unittest


class TestR390MixedNonmathOptionBindingAnalysisAndGoalAudit(unittest.TestCase):
    def test_analysis_and_goal_audit_records_small_positive_transfer(self):
        from experiment.mmlu.r390_mixed_nonmath_option_binding_analysis_and_goal_audit import build_mixed_nonmath_analysis

        summary = build_mixed_nonmath_analysis()

        self.assertEqual(summary["run_id"], "R390")
        self.assertEqual(summary["records"], 24)
        self.assertEqual(summary["arg_correct"], 19)
        self.assertEqual(summary["hybrid_correct"], 20)
        self.assertEqual(summary["delta_correct"], 1)
        self.assertEqual(summary["fixes"], 1)
        self.assertEqual(summary["harms"], 0)
        self.assertEqual(summary["wrong_forward_count"], 2)
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R385", "R386", "R387", "R388", "R389"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["mixed_nonmath_positive_no_harm"])
        self.assertTrue(summary["goal_alignment"]["hard_negative_update_required"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R391_mixed_nonmath_hard_negative_update")


if __name__ == "__main__":
    unittest.main()
