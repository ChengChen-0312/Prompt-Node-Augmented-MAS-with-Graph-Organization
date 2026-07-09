import unittest


class TestR356LearnedGraphPolicyPromptnodeDesign(unittest.TestCase):
    def test_design_makes_promptnodes_train_time_graph_actions_not_hand_templates(self):
        from experiment.mmlu.r356_learned_graph_policy_promptnode_design import build_learned_policy_design

        summary = build_learned_policy_design()

        self.assertEqual(summary["run_id"], "R356")
        self.assertEqual(summary["policy_type"], "learned_graph_policy")
        self.assertIn("ADD_PROMPT_NODE", summary["graph_actions"])
        self.assertIn("ADD_PROMPT_EDGE", summary["graph_actions"])
        self.assertIn("PRUNE_PROMPT_NODE", summary["graph_actions"])
        self.assertIn("FORWARD_CANDIDATE", summary["graph_actions"])
        self.assertIn("R322", summary["training_sources"])
        self.assertIn("R327", summary["training_sources"])
        self.assertIn("R352", summary["training_sources"])
        self.assertTrue(summary["uses_promptnode_as_first_class_graph_object"])
        self.assertTrue(summary["requires_fresh_eval_after_training"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R357_learned_graph_policy_training_manifest")


if __name__ == "__main__":
    unittest.main()
