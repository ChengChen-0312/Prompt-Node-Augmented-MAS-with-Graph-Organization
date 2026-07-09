import unittest


class TestR465LocalSmokeAfterSourceAndAuditChecklists(unittest.TestCase):
    def test_smoke_after_source_and_audit_checklists_passes(self):
        from experiment.mmlu.r465_local_smoke_after_source_and_audit_checklists import run_smoke

        summary = run_smoke()

        self.assertEqual(summary["run_id"], "R465")
        self.assertTrue(summary["local_smoke_pass"])
        self.assertEqual(summary["failed_modules"], [])
        self.assertIn("tests.test_r462_journal_template_probe", summary["tested_modules"])
        self.assertIn("tests.test_r464_external_audit_authorization_checklist", summary["tested_modules"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R466_five_run_goal_audit_after_package_checklists")


if __name__ == "__main__":
    unittest.main()
