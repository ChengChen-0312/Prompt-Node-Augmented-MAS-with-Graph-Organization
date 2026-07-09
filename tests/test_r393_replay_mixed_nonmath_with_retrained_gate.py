import unittest


class TestR393ReplayMixedNonmathWithRetrainedGate(unittest.TestCase):
    def test_replay_removes_wrong_forward_without_losing_positive_delta(self):
        from experiment.mmlu.r393_replay_mixed_nonmath_with_retrained_gate import build_replay_summary

        summary = build_replay_summary()

        self.assertEqual(summary["run_id"], "R393")
        self.assertEqual(summary["records"], 24)
        self.assertEqual(summary["arg_correct"], 19)
        self.assertEqual(summary["original_hybrid_correct"], 20)
        self.assertEqual(summary["retrained_hybrid_correct"], 20)
        self.assertEqual(summary["retrained_delta_correct"], 1)
        self.assertEqual(summary["retrained_fixes"], 1)
        self.assertEqual(summary["retrained_harms"], 0)
        self.assertEqual(summary["retrained_wrong_forward_count"], 0)
        self.assertEqual(summary["blocked_original_wrong_forward_count"], 2)
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R394_larger_mixed_nonmath_fresh_preflight")


if __name__ == "__main__":
    unittest.main()
