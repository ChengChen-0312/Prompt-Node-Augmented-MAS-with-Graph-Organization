import unittest


class TestR308GoalAuditAfterNonmath(unittest.TestCase):
    def test_goal_audit_blocks_training_until_controls_and_transfer(self):
        from experiment.mmlu.r308_goal_audit_after_nonmath import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R308")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R303", "R304", "R305", "R306", "R307"])
        self.assertTrue(summary["goal_alignment"]["aligned_with_promptnode_goal"])
        self.assertFalse(summary["claim_permissions"]["training_authorized"])
        self.assertFalse(summary["claim_permissions"]["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R309_negative_controls")


if __name__ == "__main__":
    unittest.main()
