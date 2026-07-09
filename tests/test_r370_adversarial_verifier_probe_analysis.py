import unittest


class TestR370AdversarialVerifierProbeAnalysis(unittest.TestCase):
    def test_analysis_rejects_unconstrained_domain_verifier_and_keeps_history_signal(self):
        from experiment.mmlu.r370_adversarial_verifier_probe_analysis import build_probe_analysis

        summary = build_probe_analysis()

        self.assertEqual(summary["run_id"], "R370")
        self.assertEqual(summary["adversarial_block_count"], 0)
        self.assertEqual(summary["domain_candidate_count"], 8)
        self.assertEqual(summary["domain_correct_candidate_count"], 2)
        self.assertEqual(summary["domain_candidate_precision"], 0.25)
        self.assertEqual(summary["history_domain_correct_count"], 2)
        self.assertIn("unconstrained_domain_verifier_is_unsafe", summary["root_causes"])
        self.assertFalse(summary["claim_permissions"]["integrate_unconstrained_domain_verifier"])
        self.assertTrue(summary["claim_permissions"]["history_passage_signal_allowed_for_future_preflight"])
        self.assertEqual(summary["next_required_run"], "R371_adversarial_probe_hard_negative_update")


if __name__ == "__main__":
    unittest.main()
