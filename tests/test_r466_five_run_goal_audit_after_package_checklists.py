import unittest


class TestR466FiveRunGoalAuditAfterPackageChecklists(unittest.TestCase):
    def test_goal_audit_after_package_checklists_keeps_boundaries(self):
        from experiment.mmlu.r466_five_run_goal_audit_after_package_checklists import run_audit

        summary = run_audit()

        self.assertEqual(summary["run_id"], "R466")
        self.assertEqual(summary["audited_runs"], ["R462", "R463", "R464", "R465", "R466"])
        self.assertFalse(summary["deviation_detected"])
        self.assertTrue(summary["source_package_manifested"])
        self.assertTrue(summary["external_audit_untransmitted"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R467_jcr_quartile_verification_plan")


if __name__ == "__main__":
    unittest.main()
