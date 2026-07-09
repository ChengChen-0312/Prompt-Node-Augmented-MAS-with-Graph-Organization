import unittest


class TestR448ManuscriptSnapshotAfterTables(unittest.TestCase):
    def test_snapshot_after_tables_records_tables_and_blockers(self):
        from experiment.mmlu.r448_manuscript_snapshot_after_tables import run_snapshot

        summary = run_snapshot()

        self.assertEqual(summary["run_id"], "R448")
        self.assertTrue(summary["tables_integrated"])
        self.assertIn("paper/tables/main_results.tex", summary["table_files"])
        self.assertIn("paper/tables/cost_results.tex", summary["table_files"])
        self.assertTrue(summary["local_smoke_after_tables_pass"])
        self.assertIn("external_audits_pending", summary["remaining_gaps"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R449_next_local_improvement_or_external_audit")


if __name__ == "__main__":
    unittest.main()
