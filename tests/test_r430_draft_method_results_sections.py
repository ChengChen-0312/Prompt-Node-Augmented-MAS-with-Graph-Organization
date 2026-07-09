import unittest


class TestR430DraftMethodResultsSections(unittest.TestCase):
    def test_draft_sections_include_bound_claims_and_required_caveats(self):
        from experiment.mmlu.r430_draft_method_results_sections import build_draft_sections

        summary = build_draft_sections()

        self.assertEqual(summary["run_id"], "R430")
        self.assertIn("method", summary["section_files"])
        self.assertIn("results", summary["section_files"])
        draft_text = "\n".join(summary["section_text"].values())
        self.assertIn("31/31", draft_text)
        self.assertIn("95/97", draft_text)
        self.assertIn("22/24", draft_text)
        self.assertIn("external integrity audit is pending", draft_text)
        self.assertNotIn("universal multiple-choice improvement", draft_text)
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R431_draft_claim_sanity_check")


if __name__ == "__main__":
    unittest.main()
