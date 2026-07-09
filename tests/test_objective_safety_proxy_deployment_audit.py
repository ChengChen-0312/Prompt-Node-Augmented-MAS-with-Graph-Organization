import unittest


class ObjectiveSafetyProxyDeploymentAuditTests(unittest.TestCase):
    def test_proxy_is_not_yet_a_cheap_single_template_deployment(self):
        from experiment.aqua.objective_safety_proxy_deployment_audit import (
            build_proxy_deployment_audit_summary,
        )

        summary = build_proxy_deployment_audit_summary()

        self.assertEqual(summary["rule"], "r115_objective_safety_proxy_deployment_audit")
        self.assertEqual(summary["learned_rule"], "diff_and_top_score_ge_3_or_split")
        self.assertEqual(summary["rule_feature_count"], 3)
        self.assertEqual(
            summary["rule_features"],
            [
                "objective_prediction_differs_from_baseline",
                "objective_top_score",
                "baseline_direct_votes_split",
            ],
        )
        self.assertEqual(
            summary["features_requiring_objective_guided_trace"],
            ["objective_prediction_differs_from_baseline", "objective_top_score"],
        )
        self.assertEqual(
            summary["features_requiring_arg_baseline_trace"],
            ["baseline_direct_votes_split"],
        )
        self.assertTrue(summary["requires_multiview_objective_features"])
        self.assertFalse(summary["single_template_guard_sufficient"])
        self.assertFalse(summary["cheap_single_template_deployable"])
        self.assertFalse(summary["cost_reduction_claim_ready"])
        self.assertFalse(summary["prospective_api_ready"])
        self.assertEqual(summary["input_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "deployment dependency audit only; no accuracy, cost-reduction, or API claim",
        )


if __name__ == "__main__":
    unittest.main()
