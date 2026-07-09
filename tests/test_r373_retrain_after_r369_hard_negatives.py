import unittest


class TestR373RetrainAfterR369HardNegatives(unittest.TestCase):
    def test_retraining_suppresses_r369_wrong_candidates_and_keeps_history_positives(self):
        from experiment.mmlu.r373_retrain_after_r369_hard_negatives import train_updated_policy

        summary = train_updated_policy()

        self.assertEqual(summary["run_id"], "R373")
        self.assertEqual(summary["train_records"], 241)
        self.assertEqual(summary["dev_records"], 37)
        self.assertEqual(summary["test_records"], 65)
        self.assertEqual(summary["decision_threshold"], 0.7)
        self.assertEqual(summary["dev_false_positives"], 0)
        self.assertEqual(summary["test_false_positives"], 0)
        self.assertLess(summary["r369_wrong_candidate_max_probability"], 0.7)
        self.assertGreater(summary["r369_history_positive_min_probability"], 0.9)
        self.assertTrue(summary["fresh_eval_preflight_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R374_history_guarded_fresh_eval_preflight")


if __name__ == "__main__":
    unittest.main()
