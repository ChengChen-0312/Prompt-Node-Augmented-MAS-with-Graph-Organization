import unittest


class TestR405ExperimentIntegrityLocalPrecheck(unittest.TestCase):
    def test_claim_numbers_and_boundaries_are_locally_verified(self):
        from experiment.mmlu.r405_experiment_integrity_local_precheck import build_local_precheck

        summary = build_local_precheck()

        self.assertEqual(summary["run_id"], "R405")
        self.assertEqual(summary["local_precheck_status"], "pass_external_pending")
        self.assertTrue(summary["external_review_required"])
        self.assertFalse(summary["integrity_audit_complete"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["sci_q2_ready"])

        self.assertEqual(summary["checks"]["source_files_exist"]["status"], "PASS")
        self.assertEqual(summary["checks"]["claim_number_consistency"]["status"], "PASS")
        self.assertEqual(summary["checks"]["overclaim_boundary"]["status"], "PASS")

        claim_checks = {row["id"]: row for row in summary["claim_checks"]}
        self.assertEqual(claim_checks["C1_aqua_audit_clean_gain"]["verified_values"]["baseline"], "28/31")
        self.assertEqual(claim_checks["C1_aqua_audit_clean_gain"]["verified_values"]["promptnode"], "31/31")
        self.assertEqual(claim_checks["C2_mmlu_stem_gain"]["verified_values"]["fix_harm"], "7/0")
        self.assertEqual(claim_checks["C3_history_optionbinding_pilot_gain"]["verified_values"]["arg_correct"], 21)
        self.assertEqual(claim_checks["C3_history_optionbinding_pilot_gain"]["verified_values"]["hybrid_correct"], 24)
        self.assertEqual(claim_checks["C4_mixed_nonmath_no_harm"]["verified_values"]["harms"], 0)
        self.assertEqual(claim_checks["C5_broad_general_improvement"]["boundary_action"], "forbid_as_claim")

        self.assertEqual(summary["next_required_run"], "R406_external_integrity_review_package")


if __name__ == "__main__":
    unittest.main()
