import unittest


class TestR443ManuscriptStatusSnapshot(unittest.TestCase):
    def test_snapshot_summarizes_current_manuscript_and_remaining_blockers(self):
        from experiment.mmlu.r443_manuscript_status_snapshot import run_snapshot

        summary = run_snapshot()

        self.assertEqual(summary["run_id"], "R443")
        self.assertTrue(summary["complete_initial_paper_draft"])
        self.assertTrue(summary["local_smoke_pass"])
        self.assertIn("external_experiment_integrity_audit_pending", summary["remaining_blockers"])
        self.assertIn("external_citation_audit_pending", summary["remaining_blockers"])
        self.assertIn("external_paper_claim_audit_pending", summary["remaining_blockers"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R444_external_audit_execution_plan")


if __name__ == "__main__":
    unittest.main()
