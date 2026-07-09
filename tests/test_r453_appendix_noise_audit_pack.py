import unittest
from pathlib import Path


class TestR453AppendixNoiseAuditPack(unittest.TestCase):
    def test_appendix_records_audit_clean_policy_without_silent_rewrite(self):
        from experiment.mmlu.r453_appendix_noise_audit_pack import run_pack

        summary = run_pack()
        repo = Path(__file__).resolve().parents[1]
        appendix = repo / summary["appendix_tex"]
        main_tex = (repo / "paper/main.tex").read_text(encoding="utf-8")
        appendix_text = appendix.read_text(encoding="utf-8")

        self.assertEqual(summary["run_id"], "R453")
        self.assertTrue(appendix.exists())
        self.assertIn(r"\appendix", main_tex)
        self.assertIn(r"\input{appendices/label_audit}", main_tex)
        self.assertIn("task\\_59", appendix_text)
        self.assertIn("task\\_114", appendix_text)
        self.assertIn("MMLU-high\\_school\\_physics\\_test-67", appendix_text)
        self.assertFalse(summary["silent_benchmark_rewrite"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R454_reproducibility_artifact_index")


if __name__ == "__main__":
    unittest.main()
