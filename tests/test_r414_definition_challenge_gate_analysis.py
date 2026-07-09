import unittest


class TestR414DefinitionChallengeGateAnalysis(unittest.TestCase):
    def test_analysis_allows_only_narrow_fresh_positive_claim(self):
        from experiment.mmlu.r414_definition_challenge_gate_analysis import build_definition_challenge_analysis

        summary = build_definition_challenge_analysis()

        self.assertEqual(summary["run_id"], "R414")
        self.assertEqual(summary["records"], 24)
        self.assertEqual(summary["arg_correct"], 21)
        self.assertEqual(summary["hybrid_correct"], 22)
        self.assertEqual(summary["delta_correct"], 1)
        self.assertEqual(summary["candidate_correct"], 21)
        self.assertEqual(summary["fixes"], 1)
        self.assertEqual(summary["harms"], 0)
        self.assertEqual(summary["wrong_forward_count"], 0)

        self.assertTrue(summary["selection_contribution"]["gate_improves_over_candidate_pool"])
        self.assertEqual(summary["subject_breakdown"]["moral_disputes"]["delta_correct"], 1)
        self.assertTrue(summary["claim_permissions"]["narrow_definition_challenge_claim_allowed"])
        self.assertFalse(summary["claim_permissions"]["broad_nonmath_claim_allowed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R415_update_claim_matrix_after_nonmath_positive")


if __name__ == "__main__":
    unittest.main()
