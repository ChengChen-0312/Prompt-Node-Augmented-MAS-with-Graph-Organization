import unittest


class TestR438CitationContextStaticAudit(unittest.TestCase):
    def test_static_citation_audit_passes_and_records_goal_checkpoint(self):
        from experiment.mmlu.r438_citation_context_static_audit import run_static_audit

        summary = run_static_audit()

        self.assertEqual(summary["run_id"], "R438")
        self.assertEqual(summary["missing_bib_keys"], [])
        self.assertEqual(summary["uncited_bib_keys"], [])
        self.assertGreaterEqual(summary["citation_site_count"], 8)
        self.assertTrue(summary["static_citation_pass"])
        self.assertTrue(summary["external_citation_audit_required"])
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R432", "R433", "R434", "R435", "R436"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["arg_designer_remains_main_baseline"])
        self.assertFalse(summary["final_bib_authorized"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R439_paper_static_integrity_precompile_audit")


if __name__ == "__main__":
    unittest.main()
