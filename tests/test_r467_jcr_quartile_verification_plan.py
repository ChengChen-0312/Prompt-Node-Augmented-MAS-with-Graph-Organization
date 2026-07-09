import unittest


class TestR467JcrQuartileVerificationPlan(unittest.TestCase):
    def test_jcr_plan_records_public_evidence_but_keeps_official_verification_pending(self):
        from experiment.mmlu.r467_jcr_quartile_verification_plan import run_plan

        summary = run_plan()

        self.assertEqual(summary["run_id"], "R467")
        self.assertIn("JAIR", summary["target_journals"])
        self.assertIn("KAIS", summary["target_journals"])
        self.assertFalse(summary["official_jcr_verification_completed"])
        self.assertIn("official JCR", summary["source_caveat"])
        self.assertGreaterEqual(len(summary["public_metric_sources"]), 2)
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R468_submission_readiness_matrix")


if __name__ == "__main__":
    unittest.main()
