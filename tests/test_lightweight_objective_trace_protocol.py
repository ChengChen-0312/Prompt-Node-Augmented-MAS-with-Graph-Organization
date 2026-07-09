import unittest


class LightweightObjectiveTraceProtocolTests(unittest.TestCase):
    def test_protocol_freezes_costed_lightweight_objective_trace_gates(self):
        from experiment.aqua.lightweight_objective_trace_protocol import (
            build_lightweight_objective_trace_protocol_summary,
        )

        summary = build_lightweight_objective_trace_protocol_summary()

        self.assertEqual(summary["rule"], "r117_lightweight_objective_trace_protocol")
        self.assertTrue(summary["protocol_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertEqual(summary["llm_name"], "gpt-4o-2024-08-06")
        self.assertEqual(summary["regression_tasks"], ["task_8", "task_108", "task_188", "task_250"])
        self.assertEqual(summary["required_suppressed_harm_tasks"], ["task_8"])
        self.assertEqual(summary["required_clean_recovery_tasks"], ["task_250"])
        self.assertEqual(summary["required_no_clean_harm"], True)
        self.assertEqual(summary["baseline_only_trigger_allowed"], False)
        self.assertEqual(summary["tail34_training_allowed"], False)
        self.assertEqual(summary["broad_api_allowed_before_smoke"], False)
        self.assertEqual(summary["max_promptnode_views_per_triggered_task"], 2)
        self.assertEqual(summary["full_multiview_cost_reference"], 5.050805)
        self.assertEqual(summary["measured_cost_target_upper_bound"], 1.828715)
        self.assertEqual(
            summary["candidate_protocols"],
            ["two_view_objective_probe", "graph_policy_topk_probe"],
        )
        self.assertEqual(
            summary["claim_boundary"],
            "protocol only; no new accuracy, cost, or API result",
        )


if __name__ == "__main__":
    unittest.main()
