import unittest


class TestR429PaperMethodResultsDraftPreflight(unittest.TestCase):
    def test_preflight_authorizes_bounded_method_and_results_draft(self):
        from experiment.mmlu.r429_paper_method_results_draft_preflight import build_draft_preflight

        summary = build_draft_preflight()

        self.assertEqual(summary["run_id"], "R429")
        self.assertTrue(summary["paper_draft_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertTrue(summary["external_integrity_audit_required"])
        self.assertIn("Method", summary["draft_sections_allowed"])
        self.assertIn("Results", summary["draft_sections_allowed"])
        self.assertIn("broad nonmath improvement", summary["forbidden_phrases"])
        self.assertEqual(summary["next_required_run"], "R430_draft_method_results_sections")


if __name__ == "__main__":
    unittest.main()
