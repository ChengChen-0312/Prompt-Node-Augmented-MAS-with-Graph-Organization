import unittest


class TestR455FullLocalSmokeAfterAppendixArtifact(unittest.TestCase):
    def test_recent_smoke_suite_passes_and_secret_scan_is_clean(self):
        from experiment.mmlu.r455_full_local_smoke_after_appendix_artifact import run_smoke

        summary = run_smoke()

        self.assertEqual(summary["run_id"], "R455")
        self.assertTrue(summary["local_smoke_pass"])
        self.assertEqual(summary["failed_modules"], [])
        self.assertIn("tests.test_r453_appendix_noise_audit_pack", summary["tested_modules"])
        self.assertIn("tests.test_r454_reproducibility_artifact_index", summary["tested_modules"])
        self.assertTrue(summary["secret_scan_pass"])
        self.assertEqual(summary["secret_scan_hits"], [])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R456_next_goal_audit_or_external_review_decision")


if __name__ == "__main__":
    unittest.main()
