import unittest


class TestR456NextGoalAuditOrExternalReviewDecision(unittest.TestCase):
    def test_decision_defers_external_transmission_and_keeps_goal_alignment(self):
        from experiment.mmlu.r456_next_goal_audit_or_external_review_decision import run_decision

        summary = run_decision()

        self.assertEqual(summary["run_id"], "R456")
        self.assertEqual(summary["audited_runs"], ["R452", "R453", "R454", "R455", "R456"])
        self.assertFalse(summary["deviation_detected"])
        self.assertEqual(summary["external_review_execution_decision"], "defer_until_user_confirms_transmission")
        self.assertFalse(summary["external_transmission_allowed_now"])
        self.assertTrue(summary["can_continue_local_work"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R457_static_manuscript_audit_after_appendix")


if __name__ == "__main__":
    unittest.main()
