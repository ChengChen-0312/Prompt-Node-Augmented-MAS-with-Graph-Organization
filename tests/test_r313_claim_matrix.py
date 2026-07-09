import unittest


class TestR313ClaimMatrix(unittest.TestCase):
    def test_claim_matrix_preserves_positive_and_noharm_boundaries(self):
        from experiment.mmlu.r313_claim_matrix import build_claim_matrix_summary

        summary = build_claim_matrix_summary()

        self.assertEqual(summary["run_id"], "R313")
        self.assertEqual(summary["evidence"]["aqua_audit_clean"]["proposed"], "31/31")
        self.assertEqual(summary["evidence"]["mmlu_stem_main97"]["proposed"], "95/97")
        self.assertEqual(summary["evidence"]["mmlu_nonstem_raw"]["proposed"], "34/40")
        self.assertEqual(summary["evidence"]["mmlu_nonstem_safety_replay"]["proposed"], "37/40")
        self.assertTrue(summary["claim_permissions"]["mmlu_nonstem_no_harm_allowed"])
        self.assertFalse(summary["claim_permissions"]["mmlu_nonstem_improvement_allowed"])
        self.assertFalse(summary["claim_permissions"]["training_authorized"])
        self.assertFalse(summary["claim_permissions"]["sci_q2_ready"])
        self.assertIn("remove_safety_gate", summary["required_ablations"])


if __name__ == "__main__":
    unittest.main()
