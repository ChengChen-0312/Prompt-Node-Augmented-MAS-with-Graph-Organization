import unittest


class TestR403PaperPlanUpdateAfterClaimSynthesis(unittest.TestCase):
    def test_builds_paper_plan_update_block_from_r402(self):
        from experiment.mmlu.r403_paper_plan_update_after_claim_synthesis import build_plan_update

        summary = build_plan_update()

        self.assertEqual(summary["run_id"], "R403")
        self.assertIn("C1_aqua_audit_clean_gain", summary["claim_ids"])
        self.assertIn("C4_mixed_nonmath_no_harm", summary["claim_ids"])
        self.assertIn("C5_broad_general_improvement", summary["claim_ids"])
        self.assertIn("R402 Claim Synthesis Update", summary["update_block"])
        self.assertFalse(summary["claim_permissions"]["broad_general_improvement_claim_allowed"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R404_integrity_audit_preflight")


if __name__ == "__main__":
    unittest.main()
