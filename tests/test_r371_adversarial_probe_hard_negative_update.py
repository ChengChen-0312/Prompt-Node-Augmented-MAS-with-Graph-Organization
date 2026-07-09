import unittest


class TestR371AdversarialProbeHardNegativeUpdate(unittest.TestCase):
    def test_update_adds_r369_wrong_candidates_as_hard_negatives_without_leakage(self):
        from experiment.mmlu.r371_adversarial_probe_hard_negative_update import build_updated_manifest

        rows, summary = build_updated_manifest()

        self.assertEqual(summary["run_id"], "R371")
        self.assertEqual(summary["base_records"], 334)
        self.assertEqual(summary["r369_added_records"], 9)
        self.assertEqual(summary["r369_hard_negative_records"], 7)
        self.assertEqual(summary["r369_positive_records"], 2)
        self.assertEqual(summary["manifest_records"], 343)
        self.assertTrue(summary["feature_leakage_pass"])
        self.assertFalse(any("task_id" in row for row in rows))
        self.assertFalse(any("true_answer" in row for row in rows))
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R372_goal_audit_after_adversarial_probe_update")


if __name__ == "__main__":
    unittest.main()
