import unittest


class CleanFixGraphPolicySelectorPreSmokeTests(unittest.TestCase):
    def test_presmoke_selects_high_fanin_templates_without_tail34_training(self):
        from experiment.aqua.clean_fix_graph_policy_selector_presmoke import (
            build_clean_fix_graph_policy_selector_presmoke,
        )

        rows, summary = build_clean_fix_graph_policy_selector_presmoke()

        self.assertEqual(summary["rule"], "r127_clean_fix_graph_policy_selector_presmoke")
        self.assertTrue(summary["presmoke_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertFalse(summary["uses_tail34_training_source"])
        self.assertFalse(summary["uses_tail34_outputs_for_rank_selection"])
        self.assertEqual(summary["learned_action_rule"], "diff_and_top_score_ge_3_or_split")
        self.assertEqual(summary["requested_tasks"], ["task_8", "task_108", "task_188", "task_250"])
        self.assertEqual(summary["fallback_tasks"], ["task_8", "task_188"])
        self.assertEqual(summary["switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["selected_template_ranks"], {"task_108": 5, "task_250": 5})
        self.assertEqual(summary["switches_with_update2_metadata"], 2)
        self.assertEqual(summary["switches_with_high_fanin_memory_bridge"], 2)
        self.assertEqual(summary["selector_input_field_violations"], 0)
        self.assertFalse(summary["broad_api_allowed_before_smoke"])
        self.assertTrue(summary["same_four_task_smoke_allowed_next"])
        self.assertEqual(
            summary["claim_boundary"],
            "pre-smoke selector plan only; no API, accuracy, cost, or prospective result",
        )

        by_task = {row["task_id"]: row for row in rows}
        self.assertEqual(by_task["task_8"]["planned_action"], "fallback_to_arg")
        self.assertEqual(by_task["task_188"]["planned_action"], "fallback_to_arg")
        self.assertEqual(by_task["task_108"]["planned_action"], "switch_to_promptnode_template")
        self.assertEqual(by_task["task_250"]["planned_action"], "switch_to_promptnode_template")
        self.assertEqual(by_task["task_250"]["selected_template"]["rank"], 5)
        self.assertIn("tail34_r124_outputs", summary["forbidden_training_sources"])


if __name__ == "__main__":
    unittest.main()
