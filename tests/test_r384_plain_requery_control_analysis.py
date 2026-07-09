import unittest


class TestR384PlainRequeryControlAnalysis(unittest.TestCase):
    def test_analysis_scores_strict_and_fallback_plain_control_and_audits_goal(self):
        from experiment.mmlu.r384_plain_requery_control_analysis import build_plain_requery_control_analysis

        summary = build_plain_requery_control_analysis()

        self.assertEqual(summary["run_id"], "R384")
        self.assertEqual(summary["records"], 24)
        self.assertEqual(summary["arg_correct"], 21)
        self.assertEqual(summary["option_binding_correct"], 24)
        self.assertEqual(summary["plain_strict_correct"], 14)
        self.assertEqual(summary["plain_explicit_fallback_correct"], 17)
        self.assertEqual(summary["plain_empty_label_count"], 10)
        self.assertTrue(summary["control_validity"]["strict_control_underestimates_plain"])
        self.assertTrue(summary["control_validity"]["equal_contract_control_required"])
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R379", "R380", "R381", "R382", "R383"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R385_equal_contract_plain_control_preflight")


if __name__ == "__main__":
    unittest.main()
