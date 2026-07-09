import unittest


class TestR450SubmissionGapBacklog(unittest.TestCase):
    def test_backlog_prioritizes_external_audits_and_submission_blockers(self):
        from experiment.mmlu.r450_submission_gap_backlog import run_backlog

        summary = run_backlog()

        self.assertEqual(summary["run_id"], "R450")
        self.assertGreaterEqual(len(summary["backlog_items"]), 6)
        self.assertEqual(summary["backlog_items"][0]["priority"], "P0")
        self.assertIn("external", summary["backlog_items"][0]["item"])
        self.assertIn("JAIR", summary["target_journals"])
        self.assertIn("KAIS", summary["target_journals"])
        self.assertTrue(summary["requires_user_confirmation_for_external_transmission"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R451_journal_scope_gap_matrix")


if __name__ == "__main__":
    unittest.main()
