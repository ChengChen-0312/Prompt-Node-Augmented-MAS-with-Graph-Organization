import unittest


class TestR452FiveRunGoalAuditAndCompileProbe(unittest.TestCase):
    def test_goal_audit_keeps_sci_q2_focus_and_records_compile_gap(self):
        from experiment.mmlu.r452_five_run_goal_audit_and_compile_probe import run_audit

        summary = run_audit()

        self.assertEqual(summary["run_id"], "R452")
        self.assertEqual(summary["audited_runs"], ["R447", "R448", "R449", "R450", "R451"])
        self.assertFalse(summary["deviation_detected"])
        self.assertIn("sci_q2_submission", summary["goal_alignment_tags"])
        self.assertIn("promptnode_graph_organization", summary["goal_alignment_tags"])
        self.assertIn("latex_engine_available", summary)
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R453_appendix_noise_audit_pack")


if __name__ == "__main__":
    unittest.main()
