import unittest


class TestR391MixedNonmathHardNegativeUpdate(unittest.TestCase):
    def test_update_adds_r389_fix_and_wrong_forward_rows_without_feature_leakage(self):
        from experiment.mmlu.r391_mixed_nonmath_hard_negative_update import build_updated_manifest

        rows, summary = build_updated_manifest()

        self.assertEqual(summary["run_id"], "R391")
        self.assertEqual(summary["base_records"], 343)
        self.assertEqual(summary["r389_added_records"], 3)
        self.assertEqual(summary["r389_hard_negative_records"], 2)
        self.assertEqual(summary["r389_positive_records"], 1)
        self.assertEqual(summary["manifest_records"], 346)
        self.assertTrue(summary["feature_leakage_pass"])
        self.assertFalse(any("task_id" in row for row in rows))
        self.assertFalse(any("true_answer" in row for row in rows))
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertTrue(summary["offline_retraining_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R392_retrain_after_mixed_nonmath_hard_negatives")


if __name__ == "__main__":
    unittest.main()
