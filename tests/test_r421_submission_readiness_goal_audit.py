import unittest


class TestR421SubmissionReadinessGoalAudit(unittest.TestCase):
    def test_readiness_audit_keeps_paper_not_ready_and_routes_next_gap(self):
        from experiment.mmlu.r421_submission_readiness_goal_audit import build_submission_readiness_audit

        summary = build_submission_readiness_audit()

        self.assertEqual(summary["run_id"], "R421")
        self.assertEqual(summary["readiness_verdict"], "not_ready")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R417", "R418", "R419", "R420", "R421"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["overclaiming_blocked"])
        self.assertIn("external_integrity_audit_missing", summary["blocking_gaps"])
        self.assertIn("mmlu_stem_cost_missing", summary["blocking_gaps"])
        self.assertIn("C6_definition_challenge_fresh_positive", summary["supported_or_narrow_claims"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R422_mmlu_stem_cost_reconstruction_preflight")


if __name__ == "__main__":
    unittest.main()
