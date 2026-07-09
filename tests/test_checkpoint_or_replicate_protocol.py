import unittest


class CheckpointOrReplicateProtocolTests(unittest.TestCase):
    def test_protocol_blocks_transfer_and_marks_next100_as_family_replicate(self):
        from experiment.aqua.checkpoint_or_replicate_protocol import (
            build_checkpoint_or_replicate_protocol_summary,
        )

        summary = build_checkpoint_or_replicate_protocol_summary()

        self.assertEqual(summary["rule"], "r149_transfer_checkpoint_or_aqua_replicate_protocol")
        self.assertFalse(summary["transfer_checkpoint_available"])
        self.assertFalse(summary["transfer_branch_allowed"])
        self.assertTrue(summary["aqua_next100_replicate_available"])
        self.assertEqual(summary["next100_baseline_accuracy"], "82/100")
        self.assertEqual(summary["next100_selected_accuracy"], "87/100")
        self.assertEqual(summary["next100_fix_harm"], "5/0")
        self.assertAlmostEqual(summary["next100_mcnemar_exact_p_two_sided"], 0.0625, places=6)
        self.assertFalse(summary["same_method_as_r147"])
        self.assertFalse(summary["combined_significance_claim_allowed"])
        self.assertTrue(summary["r150_goal_audit_required_next"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_protocol"], "r150_goal_audit_before_any_more_api")


if __name__ == "__main__":
    unittest.main()
