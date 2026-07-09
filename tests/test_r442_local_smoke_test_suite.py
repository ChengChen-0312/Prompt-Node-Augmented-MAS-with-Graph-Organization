import unittest


class TestR442LocalSmokeTestSuite(unittest.TestCase):
    def test_recent_r_tests_pass_as_smoke_suite(self):
        from experiment.mmlu.r442_local_smoke_test_suite import run_smoke_suite

        summary = run_smoke_suite()

        self.assertEqual(summary["run_id"], "R442")
        self.assertGreaterEqual(summary["tested_module_count"], 11)
        self.assertEqual(summary["failed_modules"], [])
        self.assertTrue(summary["local_smoke_pass"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R443_manuscript_status_snapshot")


if __name__ == "__main__":
    unittest.main()
