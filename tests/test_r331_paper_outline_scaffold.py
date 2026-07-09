import unittest
from pathlib import Path


class TestR331PaperOutlineScaffold(unittest.TestCase):
    def test_outline_scaffold_maps_claims_to_evidence_and_defers_goal_audit(self):
        from experiment.mmlu.r331_paper_outline_scaffold import build_paper_outline_scaffold, run

        summary = build_paper_outline_scaffold()
        claim_statuses = {claim["id"]: claim["status"] for claim in summary["claims_evidence_matrix"]}

        self.assertEqual(summary["run_id"], "R331")
        self.assertIn("PromptNode", summary["working_title"])
        self.assertGreaterEqual(len(summary["claims_evidence_matrix"]), 5)
        self.assertEqual(claim_statuses["C1_aqua_clean_gain"], "supported")
        self.assertEqual(claim_statuses["C2_mmlu_stem_gain"], "supported")
        self.assertEqual(claim_statuses["C5_broad_general_improvement"], "blocked")
        self.assertGreaterEqual(summary["section_count"], 6)
        self.assertLessEqual(summary["section_count"], 8)
        self.assertTrue(summary["goal_audit_due_next"])
        self.assertEqual(summary["next_required_run"], "R332_goal_audit_after_paper_scaffold")

        output = Path("PAPER_PLAN.md")
        run(output_md=str(output), summary_json="experiment/mmlu/res_logs/test_r331_summary.json", report_md="experiment/mmlu/run_logs/test_r331_report.md")
        self.assertIn("Claims-Evidence Matrix", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
