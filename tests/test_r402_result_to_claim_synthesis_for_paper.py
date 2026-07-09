import unittest


class TestR402ResultToClaimSynthesisForPaper(unittest.TestCase):
    def test_synthesis_keeps_supported_claims_narrow(self):
        from experiment.mmlu.r402_result_to_claim_synthesis_for_paper import build_claim_synthesis

        summary = build_claim_synthesis()

        self.assertEqual(summary["run_id"], "R402")
        self.assertEqual(summary["overall_claim_supported"], "partial")
        self.assertIn("C1_aqua_audit_clean_gain", summary["supported_claim_ids"])
        self.assertIn("C2_mmlu_stem_gain", summary["supported_claim_ids"])
        self.assertIn("C4_mixed_nonmath_no_harm", summary["supported_claim_ids"])
        self.assertIn("C5_broad_general_improvement", summary["unsupported_claim_ids"])
        self.assertIn("C3_history_optionbinding_pilot_gain", summary["partial_claim_ids"])
        self.assertFalse(summary["claim_permissions"]["broad_general_improvement_claim_allowed"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R403_paper_plan_update_after_claim_synthesis")


if __name__ == "__main__":
    unittest.main()
