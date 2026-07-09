import unittest


class TestR324SelectorFeatureAblation(unittest.TestCase):
    def test_feature_ablation_detects_hard_negative_gap(self):
        from experiment.mmlu.r324_selector_feature_ablation import build_feature_ablation_summary

        summary = build_feature_ablation_summary()
        variants = {row["variant"]: row for row in summary["ablation_results"]}

        self.assertEqual(summary["run_id"], "R324")
        self.assertEqual(variants["full_structural_selector"]["test_accuracy"], 1.0)
        self.assertEqual(variants["full_structural_selector"]["test_recall_forward"], 1.0)
        self.assertEqual(variants["remove_promptnode_family"]["test_accuracy"], 1.0)
        self.assertTrue(summary["hard_negative_gap_detected"])
        self.assertFalse(summary["promptedge_feature_contribution_identified"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R325_hard_negative_augmentation_protocol")


if __name__ == "__main__":
    unittest.main()
