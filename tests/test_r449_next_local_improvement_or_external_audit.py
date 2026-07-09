import unittest


class TestR449NextLocalImprovementOrExternalAudit(unittest.TestCase):
    def test_journal_target_plan_prioritizes_q2_and_external_audits(self):
        from experiment.mmlu.r449_next_local_improvement_or_external_audit import run_plan

        summary = run_plan()

        self.assertEqual(summary["run_id"], "R449")
        self.assertIn("JAIR", summary["recommended_q2_targets"][0]["short_name"])
        self.assertGreaterEqual(len(summary["recommended_q2_targets"]), 2)
        self.assertIn("external_audits", summary["next_priority_order"][0])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R450_submission_gap_backlog")


if __name__ == "__main__":
    unittest.main()
