import unittest


class TestR471FiveRunGoalAuditAfterReadinessPlanning(unittest.TestCase):
    def test_goal_audit_after_readiness_planning_keeps_blockers_visible(self):
        from experiment.mmlu.r471_five_run_goal_audit_after_readiness_planning import run_audit

        summary = run_audit()

        self.assertEqual(summary["run_id"], "R471")
        self.assertEqual(summary["audited_runs"], ["R467", "R468", "R469", "R470", "R471"])
        self.assertFalse(summary["deviation_detected"])
        self.assertIn("external audits pending", summary["visible_blockers"])
        self.assertIn("pdf compile pending", summary["visible_blockers"])
        self.assertTrue(summary["current_status_digest_exists"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R472_latex_environment_options")


if __name__ == "__main__":
    unittest.main()
