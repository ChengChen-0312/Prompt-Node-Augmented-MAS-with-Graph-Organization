import unittest


class TestR406ExternalIntegrityReviewPackage(unittest.TestCase):
    def test_package_contains_external_audit_prompt_and_goal_checkpoint(self):
        from experiment.mmlu.r406_external_integrity_review_package import build_review_package

        summary = build_review_package()

        self.assertEqual(summary["run_id"], "R406")
        self.assertTrue(summary["external_review_required"])
        self.assertFalse(summary["external_review_executed"])
        self.assertFalse(summary["integrity_audit_complete"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])

        self.assertEqual(summary["iterations_since_last_goal_check"], ["R402", "R403", "R404", "R405", "R406"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["overclaiming_blocked"])

        self.assertGreater(summary["artifact_counts"]["evaluation_scripts"], 0)
        self.assertGreater(summary["artifact_counts"]["result_files"], 0)
        self.assertGreater(summary["artifact_counts"]["paper_claims"], 0)
        self.assertIn("Ground Truth Provenance", summary["review_prompt"])
        self.assertIn("Score Normalization", summary["review_prompt"])
        self.assertIn("Result File Existence", summary["review_prompt"])
        self.assertIn("Overall verdict: PASS | WARN | FAIL", summary["review_prompt"])

        self.assertEqual(summary["next_required_run"], "R407_external_audit_or_nonmath_positive_evidence")


if __name__ == "__main__":
    unittest.main()
