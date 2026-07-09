import unittest


class TestR314GoalAudit(unittest.TestCase):
    def test_goal_audit_after_transfer_blocks_overclaiming(self):
        from experiment.mmlu.r314_goal_audit_after_transfer import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R314")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R309", "R310", "R311", "R312", "R313"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["transfer_checked"])
        self.assertFalse(summary["claim_permissions"]["broad_general_promptnode_claim_allowed"])
        self.assertFalse(summary["claim_permissions"]["training_authorized"])
        self.assertFalse(summary["claim_permissions"]["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R315_ablation_table")


if __name__ == "__main__":
    unittest.main()
