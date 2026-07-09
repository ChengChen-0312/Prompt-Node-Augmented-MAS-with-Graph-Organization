import unittest
from pathlib import Path


class TestR434FrontMatterInitialDraft(unittest.TestCase):
    def test_front_matter_draft_creates_safe_sections_and_updates_main(self):
        from experiment.mmlu.r434_front_matter_initial_draft import run_front_matter_draft

        summary = run_front_matter_draft()

        self.assertEqual(summary["run_id"], "R434")
        self.assertTrue(Path("paper/sections/0_abstract.tex").exists())
        self.assertTrue(Path("paper/sections/1_introduction.tex").exists())
        self.assertTrue(Path("paper/sections/8_conclusion.tex").exists())
        self.assertTrue(summary["abstract_word_count"] >= 120)
        self.assertEqual(summary["related_work_status"], "pending_citation_audit")
        self.assertIn("paper/sections/0_abstract.tex", summary["referenced_sections"])
        self.assertIn("paper/sections/1_introduction.tex", summary["referenced_sections"])
        self.assertIn("paper/sections/8_conclusion.tex", summary["referenced_sections"])
        self.assertNotIn("paper/sections/2_related_work.tex", summary["referenced_sections"])
        self.assertEqual(summary["remaining_forbidden_hits"], [])
        self.assertFalse(summary["complete_paper_draft"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R435_related_work_bibtex_audit_preflight")

    def test_front_matter_draft_is_repeatable_without_backup_collision(self):
        from experiment.mmlu.r434_front_matter_initial_draft import run_front_matter_draft

        first = run_front_matter_draft()
        second = run_front_matter_draft()

        self.assertEqual(first["run_id"], "R434")
        self.assertEqual(second["run_id"], "R434")
        self.assertNotEqual(first["backup_created"], second["backup_created"])


if __name__ == "__main__":
    unittest.main()
