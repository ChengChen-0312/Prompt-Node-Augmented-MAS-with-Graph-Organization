import unittest


class TestR376HistoryGuardedFreshEvalAnalysis(unittest.TestCase):
    def test_analysis_identifies_option_binding_bottleneck(self):
        from experiment.mmlu.r376_history_guarded_fresh_eval_analysis import build_history_guarded_analysis

        summary = build_history_guarded_analysis()

        self.assertEqual(summary["run_id"], "R376")
        self.assertEqual(summary["records"], 12)
        self.assertEqual(summary["arg_correct"], 6)
        self.assertEqual(summary["hybrid_correct"], 6)
        self.assertEqual(summary["delta_correct"], 0)
        self.assertEqual(summary["fixes"], 0)
        self.assertEqual(summary["harms"], 0)
        self.assertEqual(summary["gate_forward_count"], 1)
        self.assertEqual(summary["wrong_forward_count"], 1)
        self.assertGreaterEqual(summary["empty_candidate_high_confidence_count"], 5)
        self.assertIn("R377_option_binding_promptedge_replay", summary["next_required_run"])
        self.assertFalse(summary["claim_permissions"]["fresh_positive_delta_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
