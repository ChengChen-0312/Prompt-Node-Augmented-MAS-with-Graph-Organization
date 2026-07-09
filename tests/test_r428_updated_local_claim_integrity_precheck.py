import unittest


class TestR428UpdatedLocalClaimIntegrityPrecheck(unittest.TestCase):
    def test_updated_precheck_verifies_c6_and_probe_cost_without_authorizing_claims(self):
        from experiment.mmlu.r428_updated_local_claim_integrity_precheck import build_updated_local_precheck

        summary = build_updated_local_precheck()

        self.assertEqual(summary["run_id"], "R428")
        self.assertEqual(summary["checks"]["source_files_exist"]["status"], "PASS")
        self.assertEqual(summary["checks"]["claim_number_consistency"]["status"], "PASS")
        self.assertEqual(summary["checks"]["overclaim_boundary"]["status"], "PASS")
        claim_checks = {row["id"]: row for row in summary["claim_checks"]}
        self.assertIn("C6_definition_challenge_fresh_positive", claim_checks)
        self.assertEqual(claim_checks["C6_definition_challenge_fresh_positive"]["verified_values"]["hybrid_correct"], 22)
        self.assertIn("MMLU_STEM_R306_probe_estimate", summary["cost_row_checks"])
        self.assertFalse(summary["integrity_audit_complete"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertTrue(summary["paper_draft_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R429_paper_method_results_draft_preflight")


if __name__ == "__main__":
    unittest.main()
