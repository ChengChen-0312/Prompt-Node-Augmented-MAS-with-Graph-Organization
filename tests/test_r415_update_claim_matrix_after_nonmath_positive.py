import unittest


class TestR415UpdateClaimMatrixAfterNonmathPositive(unittest.TestCase):
    def test_claim_update_adds_narrow_nonmath_positive_without_overclaiming(self):
        from experiment.mmlu.r415_update_claim_matrix_after_nonmath_positive import build_claim_update

        summary = build_claim_update()

        self.assertEqual(summary["run_id"], "R415")
        claims = {claim["id"]: claim for claim in summary["claims"]}
        self.assertIn("C6_definition_challenge_fresh_positive", claims)
        self.assertEqual(claims["C6_definition_challenge_fresh_positive"]["status"], "supported_narrow")
        self.assertIn("ARG 21/24 vs DefinitionChallenge 22/24", claims["C6_definition_challenge_fresh_positive"]["evidence"])
        self.assertFalse(summary["claim_permissions"]["broad_nonmath_claim_allowed"])
        self.assertTrue(summary["claim_permissions"]["narrow_definition_challenge_claim_allowed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertTrue(summary["paper_plan_update_authorized"])
        self.assertEqual(summary["next_required_run"], "R416_cost_normalized_claim_table_and_goal_audit")


if __name__ == "__main__":
    unittest.main()
