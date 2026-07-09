import unittest


class TestR359LearnedGraphPolicySourceInvarianceAudit(unittest.TestCase):
    def test_audit_blocks_fresh_eval_when_model_uses_source_run_features(self):
        from experiment.mmlu.r359_learned_graph_policy_source_invariance_audit import build_source_invariance_audit

        summary = build_source_invariance_audit()

        self.assertEqual(summary["run_id"], "R359")
        self.assertTrue(summary["source_run_feature_risk_detected"])
        self.assertIn("source_run=R352", summary["risky_top_features"])
        self.assertFalse(summary["claim_permissions"]["fresh_eval_preflight_allowed_now"])
        self.assertTrue(summary["claim_permissions"]["source_invariant_retraining_required"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["course_correction"][0], "Remove source_run and source-specific proxy features before fresh evaluation.")
        self.assertEqual(summary["next_required_run"], "R360_source_invariant_graph_policy_retraining")


if __name__ == "__main__":
    unittest.main()
