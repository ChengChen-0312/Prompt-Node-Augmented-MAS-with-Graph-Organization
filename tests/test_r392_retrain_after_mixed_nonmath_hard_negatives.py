import unittest


class TestR392RetrainAfterMixedNonmathHardNegatives(unittest.TestCase):
    def test_weighted_retrain_suppresses_r389_wrong_forwards(self):
        from experiment.mmlu.r392_retrain_after_mixed_nonmath_hard_negatives import train_updated_policy

        summary = train_updated_policy()

        self.assertEqual(summary["run_id"], "R392")
        self.assertEqual(summary["train_records"], 244)
        self.assertEqual(summary["dev_records"], 37)
        self.assertEqual(summary["test_records"], 65)
        self.assertEqual(summary["hard_negative_weight"], 3.0)
        self.assertEqual(summary["dev_false_positives"], 0)
        self.assertEqual(summary["test_false_positives"], 0)
        self.assertLess(summary["r389_wrong_candidate_max_probability"], 0.7)
        self.assertGreater(summary["r389_positive_min_probability"], 0.85)
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R393_replay_mixed_nonmath_with_retrained_gate")


if __name__ == "__main__":
    unittest.main()
