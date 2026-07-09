import unittest


class TestR457StaticManuscriptAuditAfterAppendix(unittest.TestCase):
    def test_static_audit_accepts_appendix_integration_without_overclaim(self):
        from experiment.mmlu.r457_static_manuscript_audit_after_appendix import run_audit

        summary = run_audit()

        self.assertEqual(summary["run_id"], "R457")
        self.assertTrue(summary["appendix_integrated"])
        self.assertEqual(summary["appendix_count"], 1)
        self.assertEqual(summary["missing_inputs"], [])
        self.assertEqual(summary["todo_hits"], [])
        self.assertEqual(summary["forbidden_claim_hits"], [])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R458_caption_table_reference_polish")


if __name__ == "__main__":
    unittest.main()
