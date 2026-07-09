import unittest


class TestR459UpdatedFullLocalSmokeAfterPolish(unittest.TestCase):
    def test_updated_smoke_passes_after_caption_and_appendix_changes(self):
        from experiment.mmlu.r459_updated_full_local_smoke_after_polish import run_smoke

        summary = run_smoke()

        self.assertEqual(summary["run_id"], "R459")
        self.assertTrue(summary["local_smoke_pass"])
        self.assertEqual(summary["failed_modules"], [])
        self.assertIn("tests.test_r457_static_manuscript_audit_after_appendix", summary["tested_modules"])
        self.assertIn("tests.test_r458_caption_table_reference_polish", summary["tested_modules"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R460_manuscript_status_snapshot_after_polish")


if __name__ == "__main__":
    unittest.main()
