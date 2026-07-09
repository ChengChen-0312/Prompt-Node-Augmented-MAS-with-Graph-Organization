import unittest


class TestR323SelectorModelDryRun(unittest.TestCase):
    def test_dry_run_learns_structural_policy_without_forwarding_warning_nodes(self):
        from experiment.mmlu.r323_selector_model_dry_run import build_selector_model_summary

        summary = build_selector_model_summary()
        policy = summary["learned_policy"]

        self.assertEqual(summary["run_id"], "R323")
        self.assertIn("symbolic_verifier", policy["allowed_promptnode_families"])
        self.assertIn("nonmath_semantic", policy["allowed_promptnode_families"])
        self.assertNotIn("warning_only", policy["allowed_promptnode_families"])
        self.assertEqual(summary["forwarded_warning_only_count"], 0)
        self.assertEqual(summary["metrics"]["test"]["accuracy"], 1.0)
        self.assertEqual(summary["metrics"]["test"]["recall_forward"], 1.0)
        self.assertTrue(summary["feature_leakage_pass"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R324_selector_feature_ablation")


if __name__ == "__main__":
    unittest.main()
