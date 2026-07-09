import unittest
from pathlib import Path


class TestR470CurrentStatusDigest(unittest.TestCase):
    def test_digest_records_key_results_and_blockers(self):
        from experiment.mmlu.r470_current_status_digest import run_digest

        summary = run_digest()
        repo = Path(__file__).resolve().parents[1]
        digest = (repo / summary["digest_md"]).read_text(encoding="utf-8")

        self.assertEqual(summary["run_id"], "R470")
        self.assertIn("AQuA audit-clean: 31/31 vs 28/31", digest)
        self.assertIn("MMLU STEM: 95/97 vs 88/97", digest)
        self.assertIn("external audits pending", digest)
        self.assertTrue(summary["local_artifacts_ready"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R471_five_run_goal_audit_after_readiness_planning")


if __name__ == "__main__":
    unittest.main()
