import unittest
from pathlib import Path


class TestR433FrontMatterAndRelatedWorkPreflight(unittest.TestCase):
    def test_preflight_identifies_missing_sections_and_citation_audit(self):
        from experiment.mmlu.r433_front_matter_and_related_work_preflight import run_preflight

        summary = run_preflight()

        self.assertEqual(summary["run_id"], "R433")
        required = [
            "paper/sections/0_abstract.tex",
            "paper/sections/1_introduction.tex",
            "paper/sections/2_related_work.tex",
            "paper/sections/8_conclusion.tex",
        ]
        expected_missing = [path for path in required if not Path(path).exists()]
        self.assertEqual(summary["missing_front_matter_sections"], expected_missing)
        self.assertGreaterEqual(len(summary["local_pdf_sources"]), 6)
        self.assertGreaterEqual(len(summary["web_seed_sources"]), 4)
        self.assertIn("local", summary["research_lit_sources_contributed"])
        self.assertIn("web", summary["research_lit_sources_contributed"])
        self.assertTrue(summary["citation_audit_required_before_final_bib"])
        self.assertTrue(summary["front_matter_draft_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R434_front_matter_initial_draft")


if __name__ == "__main__":
    unittest.main()
