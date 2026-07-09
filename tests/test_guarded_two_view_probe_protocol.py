import unittest


class GuardedTwoViewProbeProtocolTests(unittest.TestCase):
    def test_protocol_corrects_r119_single_view_failure_before_more_api(self):
        from experiment.aqua.guarded_two_view_probe_protocol import (
            build_guarded_two_view_probe_protocol_summary,
        )

        summary = build_guarded_two_view_probe_protocol_summary()

        self.assertEqual(summary["rule"], "r121_guarded_two_view_or_graph_policy_probe_protocol")
        self.assertTrue(summary["protocol_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertEqual(summary["regression_tasks"], ["task_8", "task_108", "task_188", "task_250"])
        self.assertEqual(summary["max_promptnode_views_per_task"], 2)
        self.assertFalse(summary["broad_api_allowed_before_smoke"])
        self.assertTrue(summary["explicit_promptnode_evidence_required"])
        self.assertTrue(summary["strong_contract_or_two_view_agreement_required"])
        self.assertTrue(summary["blocks_direct_vote_only_switches"])
        self.assertTrue(summary["r119_clean_harm_blocked_by_protocol"])
        self.assertEqual(summary["r119_promptnode_graph_hits"], "0/4")
        self.assertEqual(summary["r119_strong_router_contract_rows"], "0/4")
        self.assertIn("guarded_router_calibrated_two_view", summary["candidate_protocols"])
        self.assertIn("train_time_graph_policy_probe", summary["candidate_protocols"])
        self.assertEqual(
            summary["claim_boundary"],
            "protocol only; no new API, accuracy, or cost result",
        )


if __name__ == "__main__":
    unittest.main()
