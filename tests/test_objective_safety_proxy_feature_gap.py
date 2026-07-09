import unittest


class ObjectiveSafetyProxyFeatureGapTests(unittest.TestCase):
    def test_existing_r078_features_do_not_cover_r109_rule_requirements(self):
        from experiment.aqua.objective_safety_proxy_feature_gap import build_feature_gap_summary

        summary = build_feature_gap_summary()

        self.assertEqual(summary["rule"], "r111_objective_safety_proxy_feature_gap")
        self.assertEqual(summary["required_feature_count"], 3)
        self.assertEqual(summary["existing_r078_feature_count"], 22)
        self.assertEqual(summary["directly_covered_required_features"], [])
        self.assertEqual(
            summary["missing_required_features"],
            [
                "objective_prediction_differs_from_baseline",
                "objective_top_score",
                "baseline_direct_votes_split",
            ],
        )
        self.assertEqual(summary["proxy_training_ready"], False)
        self.assertEqual(summary["recommended_next_artifact"], "first200_objective_safety_feature_export")
        self.assertEqual(
            summary["claim_boundary"],
            "feature coverage audit only; no proxy training or accuracy claim",
        )


if __name__ == "__main__":
    unittest.main()
