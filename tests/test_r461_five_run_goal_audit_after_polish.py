import unittest


class TestR461FiveRunGoalAuditAfterPolish(unittest.TestCase):
    def test_goal_audit_after_polish_keeps_submission_boundary(self):
        from experiment.mmlu.r461_five_run_goal_audit_after_polish import run_audit

        summary = run_audit()

        self.assertEqual(summary["run_id"], "R461")
        self.assertEqual(summary["audited_runs"], ["R457", "R458", "R459", "R460", "R461"])
        self.assertFalse(summary["deviation_detected"])
        self.assertTrue(summary["local_manuscript_artifacts_ready"])
        self.assertIn("external_audits_pending", summary["remaining_submission_blockers"])
        self.assertIn("pdf_compile_pending", summary["remaining_submission_blockers"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R462_journal_template_probe")


if __name__ == "__main__":
    unittest.main()
