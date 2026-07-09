import unittest


class TestR285GoalAuditAfterRetraining(unittest.TestCase):
    def test_goal_audit_blocks_api_when_promptnode_structure_is_not_ready(self):
        from experiment.mmlu.r285_goal_audit_after_retraining import build_goal_audit

        r281 = {"training_authorized_next": True}
        r282 = {"role_mapping_size": 6, "pn_roles_present": []}
        r283 = {"role_mapping_size": 9, "pn_roles_present": ["PN_Memory", "PN_Verifier", "PN_Router"]}
        r284 = {
            "structural_claim_supported": False,
            "arg": {"any_pn_rate": 0.0},
            "promptnode": {
                "any_pn_rate": 1.0,
                "contract_ready_rate": 0.0416666667,
                "all_pn_roles_rate": 0.125,
            },
        }

        summary = build_goal_audit(r281=r281, r282=r282, r283=r283, r284=r284)

        self.assertEqual(summary["run_id"], "R285")
        self.assertTrue(summary["no_api"])
        self.assertEqual(summary["goal_alignment"], "aligned_but_blocked_on_structure")
        self.assertFalse(summary["api_eval_allowed_next"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertIn("R286_constrained_promptnode_decoding", summary["next_runs"])
        self.assertIn("R287_promptnode_chain_retrain", summary["next_runs"])


if __name__ == "__main__":
    unittest.main()
