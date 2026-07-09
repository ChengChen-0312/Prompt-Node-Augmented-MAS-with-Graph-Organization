import unittest


class TestR358LearnedGraphPolicyOfflineTraining(unittest.TestCase):
    def test_offline_training_learns_forward_gate_without_test_false_positives(self):
        from experiment.mmlu.r358_learned_graph_policy_offline_training import train_offline_policy

        summary = train_offline_policy()

        self.assertEqual(summary["run_id"], "R358")
        self.assertEqual(summary["model"], "logistic_regression_liblinear_balanced")
        self.assertEqual(summary["train_records"], 236)
        self.assertEqual(summary["dev_records"], 35)
        self.assertEqual(summary["test_records"], 63)
        self.assertEqual(summary["test_false_positives"], 0)
        self.assertEqual(summary["test_false_negatives"], 0)
        self.assertEqual(summary["test_f1"], 1.0)
        self.assertIn("candidate_evidence_count", summary["top_positive_features"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R359_learned_graph_policy_fresh_eval_preflight")


if __name__ == "__main__":
    unittest.main()
