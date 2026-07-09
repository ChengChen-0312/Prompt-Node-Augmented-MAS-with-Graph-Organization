import unittest


class TestR327AugmentedSelectorRetrainingDryRun(unittest.TestCase):
    def test_augmented_selector_blocks_hard_negatives_and_identifies_promptedge(self):
        from experiment.mmlu.r327_augmented_selector_retraining_dry_run import build_augmented_selector_summary

        summary = build_augmented_selector_summary()
        ablations = {row["variant"]: row for row in summary["feature_ablation_after_hard_negatives"]}

        self.assertEqual(summary["run_id"], "R327")
        self.assertEqual(summary["manifest_records"], 238)
        self.assertEqual(summary["hard_negative_records"], 4)
        self.assertEqual(summary["metrics"]["test"]["accuracy"], 1.0)
        self.assertEqual(summary["forwarded_hard_negative_count"], 0)
        self.assertEqual(ablations["no_family_no_promptedge_text_feature"]["test_false_forward"], 1)
        self.assertEqual(ablations["no_family_with_promptedge_text_feature"]["test_false_forward"], 0)
        self.assertTrue(summary["promptedge_feature_contribution_identified"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R328_selector_policy_claim_update")


if __name__ == "__main__":
    unittest.main()
