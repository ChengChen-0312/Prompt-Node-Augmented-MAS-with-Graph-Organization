import unittest


class TestR447LocalSmokeAfterTables(unittest.TestCase):
    def test_smoke_after_tables_passes_and_records_goal_checkpoint(self):
        from experiment.mmlu.r447_local_smoke_after_tables import run_smoke

        summary = run_smoke()

        self.assertEqual(summary["run_id"], "R447")
        self.assertTrue(summary["local_smoke_pass"])
        self.assertEqual(summary["failed_modules"], [])
        self.assertIn("tests.test_r446_local_tables_and_submission_gaps", summary["tested_modules"])
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R442", "R443", "R444", "R445", "R446"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R448_manuscript_snapshot_after_tables")


if __name__ == "__main__":
    unittest.main()
