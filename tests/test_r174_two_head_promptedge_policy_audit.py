import unittest


class R174TwoHeadPromptEdgePolicyAuditTests(unittest.TestCase):
    def test_two_head_targets_split_insertion_from_override(self):
        from experiment.aqua.r174_two_head_promptedge_policy_audit import (
            add_two_head_targets,
        )

        rows = add_two_head_targets(
            [
                {"selective_action": "preserve_safe_insert"},
                {"selective_action": "switch_critical_insert"},
                {"selective_action": "suppress_or_fallback"},
            ]
        )

        self.assertEqual(
            [(row["insertion_target"], row["override_target"]) for row in rows],
            [(1, 0), (1, 1), (0, 0)],
        )
        self.assertEqual(
            [row["deployment_action"] for row in rows],
            ["insert_observe_only", "insert_switch_allowed", "fallback_to_arg"],
        )

    def test_real_r166_rows_show_override_data_insufficiency(self):
        from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows
        from experiment.aqua.r174_two_head_promptedge_policy_audit import (
            build_two_head_summary,
        )

        rows = load_jsonl_rows(
            "experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl"
        )
        summary = build_two_head_summary(rows)

        self.assertEqual(summary["source_rows"], 800)
        self.assertEqual(summary["target_counts"]["insertion_positive"], 76)
        self.assertEqual(summary["target_counts"]["override_positive"], 4)
        self.assertTrue(summary["override_head"]["data_insufficient"])
        self.assertFalse(summary["override_head"]["learned_head_claim_supported"])


if __name__ == "__main__":
    unittest.main()
