import unittest


class R176SwitchCriticalTargetMiningTests(unittest.TestCase):
    def test_classifies_confirmed_weak_and_no_promptnode_switch_gaps(self):
        from experiment.aqua.r176_switch_critical_target_mining import (
            classify_switch_gap,
        )

        confirmed = classify_switch_gap(
            {"target_action": "switch_to_objective"},
            [
                {
                    "is_r166_switch_critical": True,
                    "candidate_method": "candidate",
                    "objective_bucket": "preferred_graph",
                    "objective_reward": 9,
                    "score_margin_to_next": 4,
                    "num_prompt_nodes": 3,
                    "has_promptnode_edge_permissions": True,
                }
            ],
        )
        weak = classify_switch_gap(
            {"target_action": "switch_to_objective"},
            [
                {
                    "is_r166_switch_critical": False,
                    "candidate_method": "router",
                    "objective_bucket": "multi_view_tie",
                    "objective_reward": 11,
                    "score_margin_to_next": 8,
                    "num_prompt_nodes": 3,
                    "has_promptnode_edge_permissions": True,
                }
            ],
        )
        no_promptnode = classify_switch_gap(
            {"target_action": "switch_to_objective"},
            [
                {
                    "is_r166_switch_critical": False,
                    "candidate_method": "candidate",
                    "objective_bucket": "low_margin_top",
                    "objective_reward": 3,
                    "score_margin_to_next": 2,
                    "num_prompt_nodes": 0,
                    "has_promptnode_edge_permissions": False,
                }
            ],
        )

        self.assertEqual(confirmed["gap_class"], "confirmed_switch_critical")
        self.assertEqual(weak["gap_class"], "weak_high_margin_tie_candidate")
        self.assertEqual(no_promptnode["gap_class"], "no_promptnode_candidate")
        self.assertFalse(weak["claimable_override_label"])

    def test_real_first200_switch_pool_remains_too_sparse_after_weak_expansion(self):
        from experiment.aqua.r176_switch_critical_target_mining import build_mining_summary

        summary = build_mining_summary(
            "experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl",
            "experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl",
            "experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl",
        )

        self.assertEqual(summary["r112_switch_rows"], 11)
        self.assertEqual(summary["gap_class_counts"]["confirmed_switch_critical"], 4)
        self.assertEqual(summary["gap_class_counts"]["weak_high_margin_tie_candidate"], 2)
        self.assertTrue(summary["expanded_override_pool_still_insufficient"])


if __name__ == "__main__":
    unittest.main()
