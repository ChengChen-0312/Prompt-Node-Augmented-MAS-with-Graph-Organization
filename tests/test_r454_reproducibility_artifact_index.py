import unittest
from pathlib import Path


class TestR454ReproducibilityArtifactIndex(unittest.TestCase):
    def test_reproducibility_index_lists_artifacts_without_secret_values(self):
        from experiment.mmlu.r454_reproducibility_artifact_index import run_index

        summary = run_index()
        repo = Path(__file__).resolve().parents[1]
        artifact = repo / summary["artifact_index_md"]
        text = artifact.read_text(encoding="utf-8")

        self.assertEqual(summary["run_id"], "R454")
        self.assertTrue(artifact.exists())
        self.assertIn("gpt-4o-2024-08-06", text)
        self.assertIn("aqua_tail34_r271_final_claim_table_summary.json", text)
        self.assertIn("mmlu_r321_paper_evidence_table_and_training_gate_summary.json", text)
        self.assertTrue(summary["api_key_values_redacted"])
        self.assertNotIn("sk-", text)
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R455_full_local_smoke_after_appendix_artifact")


if __name__ == "__main__":
    unittest.main()
