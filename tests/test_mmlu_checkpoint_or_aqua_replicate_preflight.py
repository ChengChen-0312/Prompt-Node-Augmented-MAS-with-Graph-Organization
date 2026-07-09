import unittest


class MMLUCheckpointOrAquaReplicatePreflightTests(unittest.TestCase):
    def test_blocks_transfer_and_true_aqua_replicate_without_checkpoint_or_unseen_rows(self):
        from experiment.aqua.mmlu_checkpoint_or_aqua_replicate_preflight import (
            build_preflight_summary,
        )

        summary = build_preflight_summary()

        self.assertEqual(
            summary["rule"],
            "r152_mmlu_checkpoint_resolution_or_aqua_same_method_replicate_preflight",
        )
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["mmlu_transfer_data_ready"])
        self.assertFalse(summary["compatible_mmlu_arg_checkpoint_available"])
        self.assertFalse(summary["transfer_branch_allowed"])
        self.assertEqual(summary["aqua_dataset_rows"], 254)
        self.assertEqual(summary["aqua_unseen_row_count"], 0)
        self.assertFalse(summary["independent_same_method_aqua_replicate_ready"])
        self.assertEqual(
            summary["same_method_aqua_replicate_blocker"],
            "no_unseen_aqua_rows_and_next100_used_in_r112_rule_training",
        )
        self.assertEqual(
            summary["chosen_next_work"],
            "r153_mmlu_checkpoint_build_or_import_protocol",
        )
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_goal_audit_due"], "R155")


if __name__ == "__main__":
    unittest.main()
