import unittest


class ObjectiveSafetyFirst200FeatureExportTests(unittest.TestCase):
    def test_exports_non_tail34_rule_inputs_for_objective_safety_proxy(self):
        from experiment.aqua.objective_safety_first200_feature_export import (
            build_first200_feature_export,
        )

        rows, summary = build_first200_feature_export()

        self.assertEqual(summary["rule"], "r112_first200_objective_safety_feature_export")
        self.assertEqual(summary["num_rows"], 200)
        self.assertEqual(len(rows), 200)
        self.assertEqual(summary["required_rule_feature_count"], 3)
        self.assertEqual(summary["exported_required_rule_features"], summary["required_rule_features"])
        self.assertEqual(summary["missing_required_rule_features"], [])
        self.assertEqual(summary["baseline_source_rows"], 200)
        self.assertEqual(summary["objective_source_rows"], 200)
        self.assertFalse(summary["uses_tail34_training_source"])
        self.assertEqual(summary["policy_input_field_violations"], 0)
        self.assertEqual(summary["target_action_counts"], {"fallback_to_arg": 189, "switch_to_objective": 11})
        self.assertEqual(
            summary["target_reason_counts"],
            {
                "baseline_direct_split_allows_switch": 1,
                "insufficient_safety_evidence": 9,
                "objective_top_score_ge3": 10,
                "same_prediction_as_arg": 180,
            },
        )
        self.assertEqual(summary["objective_prediction_differs_count"], 20)
        self.assertEqual(summary["baseline_direct_votes_split_count"], 3)
        self.assertEqual(summary["switch_target_count"], 11)
        self.assertEqual(
            summary["switch_target_tasks"],
            [
                "task_152",
                "task_172",
                "task_95",
                "task_135",
                "task_122",
                "task_149",
                "task_176",
                "task_184",
                "task_197",
                "task_67",
                "task_207",
            ],
        )
        self.assertEqual(
            summary["claim_boundary"],
            "first200 feature export and proxy target construction only; no trained proxy or accuracy claim",
        )


if __name__ == "__main__":
    unittest.main()
