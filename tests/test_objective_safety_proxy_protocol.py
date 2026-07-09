import unittest


class ObjectiveSafetyProxyProtocolTests(unittest.TestCase):
    def test_protocol_blocks_tail34_training_and_freezes_proxy_requirements(self):
        from experiment.aqua.objective_safety_proxy_protocol import build_proxy_protocol_summary

        summary = build_proxy_protocol_summary()

        self.assertEqual(summary["rule"], "r110_objective_safety_proxy_protocol")
        self.assertEqual(summary["train_source_rows"], 800)
        self.assertEqual(summary["train_clean_fix_preserve_rows"], 76)
        self.assertEqual(summary["existing_selector_eval_agreement"], 0.9675)
        self.assertEqual(summary["tail34_eval_target_rows"], 34)
        self.assertEqual(summary["tail34_training_allowed"], False)
        self.assertEqual(
            summary["required_rule_features"],
            [
                "objective_prediction_differs_from_baseline",
                "objective_top_score",
                "baseline_direct_votes_split",
            ],
        )
        self.assertEqual(
            summary["proxy_candidate_families"],
            ["lightweight_multiview_objective", "graph_policy_selector"],
        )
        self.assertEqual(summary["input_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "protocol only; no trained proxy, accuracy, or SCI claim",
        )


if __name__ == "__main__":
    unittest.main()
