import unittest


class TestR441ExternalAuditPackageRefresh(unittest.TestCase):
    def test_refreshes_external_audit_packages_and_goal_checkpoint(self):
        from experiment.mmlu.r441_external_audit_package_refresh import run_refresh

        summary = run_refresh()

        self.assertEqual(summary["run_id"], "R441")
        self.assertEqual(
            sorted(summary["audit_packages"].keys()),
            ["citation_context_audit", "experiment_integrity_audit", "paper_claim_audit"],
        )
        self.assertTrue(summary["audit_packages"]["citation_context_audit"]["prompt_md"].endswith(".md"))
        self.assertTrue(summary["audit_packages"]["paper_claim_audit"]["prompt_md"].endswith(".md"))
        self.assertEqual(summary["external_reviews_executed"], [])
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R437", "R438", "R439", "R440", "R441"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R442_local_smoke_test_suite")


if __name__ == "__main__":
    unittest.main()
