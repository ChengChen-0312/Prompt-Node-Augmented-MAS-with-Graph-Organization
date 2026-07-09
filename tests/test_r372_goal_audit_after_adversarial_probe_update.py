import unittest


class TestR372GoalAuditAfterAdversarialProbeUpdate(unittest.TestCase):
    def test_goal_audit_authorizes_retraining_not_more_api(self):
        from experiment.mmlu.r372_goal_audit_after_adversarial_probe_update import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R372")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R367", "R368", "R369", "R370", "R371"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["adversarial_probe_failed_safely"])
        self.assertTrue(summary["goal_alignment"]["hard_negative_update_done"])
        self.assertTrue(summary["goal_alignment"]["history_signal_preserved"])
        self.assertTrue(summary["claim_permissions"]["offline_retraining_allowed"])
        self.assertFalse(summary["claim_permissions"]["api_execution_allowed_now"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R373_retrain_after_r369_hard_negatives")


if __name__ == "__main__":
    unittest.main()
