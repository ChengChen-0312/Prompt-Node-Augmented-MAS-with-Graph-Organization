import unittest


class ObjectiveSafetyRuleDistillationTests(unittest.TestCase):
    def test_distilled_rule_matches_r096_targets_and_records_feature_dependency(self):
        from experiment.aqua.objective_safety_rule_distillation import build_distillation_summary

        summary = build_distillation_summary()

        self.assertEqual(summary["rule"], "r109_objective_safety_rule_distillation")
        self.assertEqual(summary["num_rows"], 34)
        self.assertEqual(summary["target_agreement"], "34/34")
        self.assertEqual(summary["switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["objective_diff_suppressed_tasks"], ["task_114", "task_59"])
        self.assertEqual(summary["rule_input_field_violations"], 0)
        self.assertEqual(summary["requires_multiview_objective_features"], True)
        self.assertEqual(summary["cheap_single_template_proxy_ready"], False)
        self.assertEqual(
            summary["claim_boundary"],
            "rule distillation over R096 targets; no new accuracy or cheap-proxy claim",
        )


if __name__ == "__main__":
    unittest.main()
