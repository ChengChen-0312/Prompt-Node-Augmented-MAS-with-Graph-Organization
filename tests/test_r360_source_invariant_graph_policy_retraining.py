import unittest


class TestR360SourceInvariantGraphPolicyRetraining(unittest.TestCase):
    def test_source_invariant_retraining_removes_source_features_and_uses_conservative_threshold(self):
        from experiment.mmlu.r360_source_invariant_graph_policy_retraining import train_source_invariant_policy

        summary = train_source_invariant_policy()

        self.assertEqual(summary["run_id"], "R360")
        self.assertTrue(summary["source_features_removed"])
        self.assertEqual(summary["decision_threshold"], 0.7)
        self.assertEqual(summary["dev_false_positives"], 0)
        self.assertEqual(summary["dev_false_negatives"], 0)
        self.assertEqual(summary["test_false_positives"], 0)
        self.assertEqual(summary["test_false_negatives"], 0)
        self.assertFalse(any(feature.startswith("source_run=") for feature in summary["top_positive_features"]))
        self.assertTrue(summary["fresh_eval_preflight_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R361_goal_audit_after_source_invariant_policy")


if __name__ == "__main__":
    unittest.main()
