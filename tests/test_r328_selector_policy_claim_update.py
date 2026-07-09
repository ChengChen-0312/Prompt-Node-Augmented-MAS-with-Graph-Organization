import unittest


class TestR328SelectorPolicyClaimUpdate(unittest.TestCase):
    def test_selector_claim_update_allows_feasibility_but_blocks_accuracy_claim(self):
        from experiment.mmlu.r328_selector_policy_claim_update import build_selector_claim_update

        summary = build_selector_claim_update()
        permissions = summary["selector_claim_permissions"]

        self.assertEqual(summary["run_id"], "R328")
        self.assertTrue(permissions["offline_selector_feasibility_claim_allowed"])
        self.assertTrue(permissions["promptedge_safety_feature_claim_allowed"])
        self.assertFalse(permissions["external_accuracy_improvement_claim_allowed"])
        self.assertFalse(permissions["api_execution_allowed"])
        self.assertFalse(permissions["sci_q2_ready"])
        self.assertEqual(summary["evidence"]["r327_augmented_selector"]["test_accuracy"], 1.0)
        self.assertEqual(summary["evidence"]["r327_promptedge_ablation"]["false_forward_without_edge_text"], 1)
        self.assertEqual(summary["next_required_run"], "R329_case_study_extraction")


if __name__ == "__main__":
    unittest.main()
