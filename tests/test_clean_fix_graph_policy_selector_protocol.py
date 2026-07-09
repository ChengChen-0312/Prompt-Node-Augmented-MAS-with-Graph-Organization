import unittest


class CleanFixGraphPolicySelectorProtocolTests(unittest.TestCase):
    def test_protocol_uses_non_tail34_training_sources_before_next_smoke(self):
        from experiment.aqua.clean_fix_graph_policy_selector_protocol import (
            build_clean_fix_graph_policy_selector_protocol,
        )

        summary = build_clean_fix_graph_policy_selector_protocol()

        self.assertEqual(summary["rule"], "r126_clean_fix_graph_policy_selector_protocol")
        self.assertTrue(summary["protocol_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertEqual(summary["first200_template_count"], 17)
        self.assertEqual(summary["first200_clean_fix_positive_rows"], 76)
        self.assertEqual(summary["first200_objective_safety_rows"], 200)
        self.assertFalse(summary["uses_tail34_training_source"])
        self.assertEqual(summary["required_clean_harm_guards"], ["task_8", "task_188"])
        self.assertEqual(summary["required_clean_recovery_targets"], ["task_250"])
        self.assertEqual(summary["noisy_optional_targets"], ["task_108"])
        self.assertIn("graph_policy_selector", summary["candidate_selector_families"])
        self.assertIn("template_rank_policy", summary["candidate_selector_families"])
        self.assertIn("tail34_r124_outputs", summary["forbidden_training_sources"])
        self.assertFalse(summary["broad_api_allowed_before_smoke"])
        self.assertEqual(
            summary["next_smoke_protocol"],
            "four_task_clean_fix_graph_policy_selector_smoke",
        )
        self.assertEqual(
            summary["claim_boundary"],
            "protocol only; no training, API, accuracy, or cost result",
        )


if __name__ == "__main__":
    unittest.main()
