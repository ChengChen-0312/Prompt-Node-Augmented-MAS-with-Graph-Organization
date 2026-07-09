import unittest


class TestR357LearnedGraphPolicyTrainingManifest(unittest.TestCase):
    def test_manifest_adds_tool_promptnode_positives_and_fresh_zero_coverage_negatives_without_leakage(self):
        from experiment.mmlu.r357_learned_graph_policy_training_manifest import build_training_manifest

        rows, summary = build_training_manifest()

        self.assertEqual(summary["run_id"], "R357")
        self.assertEqual(summary["base_augmented_records"], 238)
        self.assertEqual(summary["r352_added_records"], 48)
        self.assertEqual(summary["r354_added_records"], 48)
        self.assertEqual(summary["manifest_records"], 334)
        self.assertGreaterEqual(summary["positive_forward_targets"], 20)
        self.assertIn("R352", summary["source_run_counts"])
        self.assertIn("R354", summary["source_run_counts"])
        self.assertTrue(summary["feature_leakage_pass"])
        self.assertTrue(summary["contains_first_class_graph_action_targets"])
        self.assertFalse(any("task_id" in row for row in rows))
        self.assertFalse(any("true_answer" in row for row in rows))
        self.assertEqual(summary["next_required_run"], "R358_learned_graph_policy_offline_training")


if __name__ == "__main__":
    unittest.main()
