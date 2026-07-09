import unittest
from pathlib import Path


class TestR446LocalTablesAndSubmissionGaps(unittest.TestCase):
    def test_generates_result_tables_and_keeps_submission_gaps_explicit(self):
        from experiment.mmlu.r446_local_tables_and_submission_gaps import run_tables

        summary = run_tables()

        self.assertEqual(summary["run_id"], "R446")
        self.assertTrue(Path("paper/tables/main_results.tex").exists())
        self.assertTrue(Path("paper/tables/cost_results.tex").exists())
        self.assertGreaterEqual(summary["main_result_rows"], 5)
        self.assertGreaterEqual(summary["cost_rows"], 5)
        self.assertNotIn(r"\\_", Path("paper/tables/main_results.tex").read_text(encoding="utf-8"))
        self.assertNotIn(r"\\_", Path("paper/tables/cost_results.tex").read_text(encoding="utf-8"))
        results_text = Path("paper/sections/5_results.tex").read_text(encoding="utf-8")
        self.assertIn(r"\input{tables/main_results}", results_text)
        self.assertIn(r"\input{tables/cost_results}", results_text)
        self.assertIn("external_audits_pending", summary["submission_gaps"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R447_local_smoke_after_tables")


if __name__ == "__main__":
    unittest.main()
