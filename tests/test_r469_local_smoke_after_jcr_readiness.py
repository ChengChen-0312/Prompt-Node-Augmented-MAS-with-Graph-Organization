import unittest


class TestR469LocalSmokeAfterJcrReadiness(unittest.TestCase):
    def test_smoke_after_jcr_and_readiness_artifacts_passes(self):
        from experiment.mmlu.r469_local_smoke_after_jcr_readiness import run_smoke

        summary = run_smoke()

        self.assertEqual(summary["run_id"], "R469")
        self.assertTrue(summary["local_smoke_pass"])
        self.assertEqual(summary["failed_modules"], [])
        self.assertIn("tests.test_r467_jcr_quartile_verification_plan", summary["tested_modules"])
        self.assertIn("tests.test_r468_submission_readiness_matrix", summary["tested_modules"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R470_current_status_digest")


if __name__ == "__main__":
    unittest.main()
