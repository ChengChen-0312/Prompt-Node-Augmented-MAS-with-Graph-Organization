import unittest
from pathlib import Path


class TestR458CaptionTableReferencePolish(unittest.TestCase):
    def test_table_captions_and_result_references_are_claim_bounded(self):
        from experiment.mmlu.r458_caption_table_reference_polish import run_polish

        summary = run_polish()
        repo = Path(__file__).resolve().parents[1]
        main_table = (repo / "paper/tables/main_results.tex").read_text(encoding="utf-8")
        cost_table = (repo / "paper/tables/cost_results.tex").read_text(encoding="utf-8")
        results = (repo / "paper/sections/5_results.tex").read_text(encoding="utf-8")

        self.assertEqual(summary["run_id"], "R458")
        self.assertIn("split-scoped", main_table)
        self.assertIn("not universal", main_table)
        self.assertIn("probe estimate", cost_table)
        self.assertIn(r"Table~\ref{tab:main-results}", results)
        self.assertIn(r"Table~\ref{tab:cost-results}", results)
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R459_updated_full_local_smoke_after_polish")


if __name__ == "__main__":
    unittest.main()
