import unittest
from pathlib import Path


class TestR436CitationMetadataFetchAndBibSkeleton(unittest.TestCase):
    def test_fetch_writes_bib_skeleton_but_keeps_final_audit_required(self):
        from experiment.mmlu.r436_citation_metadata_fetch_and_bib_skeleton import run_fetch

        summary = run_fetch()

        bib_path = Path(summary["references_bib"])
        self.assertEqual(summary["run_id"], "R436")
        self.assertTrue(bib_path.exists())
        self.assertGreaterEqual(summary["fetched_bib_count"], 8)
        self.assertEqual(summary["bib_entry_count"], summary["fetched_bib_count"])
        self.assertTrue(summary["all_entries_have_source_url"])
        self.assertTrue(summary["citation_audit_required_before_use"])
        self.assertFalse(summary["final_bib_authorized"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertIn("@", bib_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["next_required_run"], "R437_related_work_initial_draft")


if __name__ == "__main__":
    unittest.main()
