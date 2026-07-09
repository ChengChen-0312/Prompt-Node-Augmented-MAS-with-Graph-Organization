import json
import unittest
from pathlib import Path


class TestR435RelatedWorkBibtexAuditPreflight(unittest.TestCase):
    def test_preflight_writes_candidate_papers_without_authorizing_bib(self):
        from experiment.mmlu.r435_related_work_bibtex_audit_preflight import run_preflight

        summary = run_preflight()

        candidate_path = Path(summary["candidate_papers_json"])
        self.assertEqual(summary["run_id"], "R435")
        self.assertTrue(candidate_path.exists())
        candidates = json.loads(candidate_path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(candidates), 8)
        self.assertEqual(summary["candidate_count"], len(candidates))
        self.assertIn("ARG-Designer", summary["required_related_work_topics"])
        self.assertIn("Agent pruning/dropout", summary["required_related_work_topics"])
        self.assertIn("Graph prompt learning", summary["required_related_work_topics"])
        self.assertTrue(summary["verify_papers_required_next"])
        self.assertFalse(summary["final_bib_authorized"])
        self.assertFalse(summary["related_work_draft_authorized"])
        self.assertEqual(summary["next_required_run"], "R436_citation_metadata_fetch_and_bib_skeleton")


if __name__ == "__main__":
    unittest.main()
