import unittest


class TestR460ManuscriptStatusSnapshotAfterPolish(unittest.TestCase):
    def test_snapshot_records_ready_local_artifacts_and_remaining_blockers(self):
        from experiment.mmlu.r460_manuscript_status_snapshot_after_polish import run_snapshot

        summary = run_snapshot()

        self.assertEqual(summary["run_id"], "R460")
        self.assertTrue(summary["appendix_integrated"])
        self.assertTrue(summary["artifact_index_exists"])
        self.assertTrue(summary["local_smoke_after_polish_pass"])
        self.assertIn("external_experiment_integrity_audit_pending", summary["remaining_blockers"])
        self.assertIn("latex_engine_missing_for_pdf_compile", summary["remaining_blockers"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R461_five_run_goal_audit_after_polish")


if __name__ == "__main__":
    unittest.main()
