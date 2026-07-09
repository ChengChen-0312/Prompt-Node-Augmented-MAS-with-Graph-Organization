import unittest
from pathlib import Path


class TestR437RelatedWorkInitialDraft(unittest.TestCase):
    def test_related_work_draft_uses_fetched_keys_and_updates_main(self):
        from experiment.mmlu.r437_related_work_initial_draft import run_related_work_draft

        summary = run_related_work_draft()

        related = Path("paper/sections/2_related_work.tex")
        main = Path("paper/main.tex")
        self.assertEqual(summary["run_id"], "R437")
        self.assertTrue(related.exists())
        self.assertIn("paper/sections/2_related_work.tex", summary["referenced_sections"])
        self.assertGreaterEqual(len(summary["citation_keys_used"]), 8)
        self.assertEqual(summary["missing_bib_keys"], [])
        self.assertEqual(summary["remaining_forbidden_hits"], [])
        self.assertIn(r"\input{sections/2_related_work}", main.read_text(encoding="utf-8"))
        self.assertIn(r"\bibliography{references}", main.read_text(encoding="utf-8"))
        self.assertTrue(summary["complete_initial_paper_draft"])
        self.assertTrue(summary["citation_context_audit_required_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R438_citation_context_static_audit")


if __name__ == "__main__":
    unittest.main()
