import unittest


class TestR377OptionBindingPromptEdgeReplay(unittest.TestCase):
    def test_option_binding_edge_replay_repairs_one_without_harm(self):
        from experiment.mmlu.r377_option_binding_promptedge_replay import build_option_binding_replay

        summary = build_option_binding_replay()

        self.assertEqual(summary["run_id"], "R377")
        self.assertEqual(summary["records"], 12)
        self.assertEqual(summary["arg_correct"], 6)
        self.assertEqual(summary["r375_hybrid_correct"], 6)
        self.assertEqual(summary["edge_hybrid_correct"], 7)
        self.assertEqual(summary["delta_vs_arg"], 1)
        self.assertEqual(summary["delta_vs_r375"], 1)
        self.assertEqual(summary["fixes"], 1)
        self.assertEqual(summary["harms"], 0)
        self.assertEqual(summary["wrong_forward_count"], 0)
        self.assertGreaterEqual(summary["bound_candidate_count"], 2)
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R378_goal_audit_after_option_binding_promptedge")


if __name__ == "__main__":
    unittest.main()
