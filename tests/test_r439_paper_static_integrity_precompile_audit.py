import unittest


class TestR439PaperStaticIntegrityPrecompileAudit(unittest.TestCase):
    def test_precompile_static_audit_reports_blockers_without_claim_authorization(self):
        from experiment.mmlu.r439_paper_static_integrity_precompile_audit import run_precompile_audit

        summary = run_precompile_audit()

        self.assertEqual(summary["run_id"], "R439")
        self.assertTrue(summary["all_referenced_sections_exist"])
        self.assertEqual(summary["stale_section_files"], [])
        self.assertEqual(summary["remaining_forbidden_hits"], [])
        self.assertEqual(summary["todo_hits"], [])
        self.assertIn("external_experiment_integrity_audit_pending", summary["submission_blockers"])
        self.assertIn("external_citation_audit_pending", summary["submission_blockers"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R440_paper_claim_number_static_audit")


if __name__ == "__main__":
    unittest.main()
