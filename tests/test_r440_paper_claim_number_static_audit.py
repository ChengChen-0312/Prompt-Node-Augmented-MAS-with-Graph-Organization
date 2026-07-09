import unittest


class TestR440PaperClaimNumberStaticAudit(unittest.TestCase):
    def test_static_number_claims_match_known_result_files(self):
        from experiment.mmlu.r440_paper_claim_number_static_audit import run_number_audit

        summary = run_number_audit()

        self.assertEqual(summary["run_id"], "R440")
        self.assertGreaterEqual(summary["claim_count"], 10)
        self.assertEqual(summary["mismatches"], [])
        self.assertEqual(summary["unsupported_claims"], [])
        self.assertTrue(summary["static_number_audit_pass"])
        self.assertTrue(summary["external_paper_claim_audit_required"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R441_external_audit_package_refresh")


if __name__ == "__main__":
    unittest.main()
