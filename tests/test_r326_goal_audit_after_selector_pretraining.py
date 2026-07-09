import unittest


class TestR326GoalAuditAfterSelectorPretraining(unittest.TestCase):
    def test_goal_audit_after_selector_pretraining_keeps_training_claim_blocked(self):
        from experiment.mmlu.r326_goal_audit_after_selector_pretraining import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R326")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R321", "R322", "R323", "R324", "R325"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["selector_manifest_frozen_without_leakage"])
        self.assertTrue(summary["goal_alignment"]["hard_negative_gap_detected_and_addressed"])
        self.assertTrue(summary["claim_permissions"]["offline_selector_retraining_allowed"])
        self.assertFalse(summary["claim_permissions"]["api_execution_allowed"])
        self.assertFalse(summary["claim_permissions"]["selector_training_paper_claim_allowed"])
        self.assertFalse(summary["claim_permissions"]["broad_general_promptnode_claim_allowed"])
        self.assertFalse(summary["claim_permissions"]["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R327_augmented_selector_retraining_dry_run")


if __name__ == "__main__":
    unittest.main()
