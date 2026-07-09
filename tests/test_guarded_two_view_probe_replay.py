import unittest


class GuardedTwoViewProbeReplayTests(unittest.TestCase):
    def test_guard_rejects_existing_objective_switches_without_promptnode_evidence(self):
        from experiment.aqua.guarded_two_view_probe_replay import (
            build_guarded_two_view_probe_replay_summary,
        )

        summary = build_guarded_two_view_probe_replay_summary()

        self.assertEqual(summary["rule"], "r122_guarded_two_view_probe_replay")
        self.assertTrue(summary["replay_only"])
        self.assertEqual(summary["total_tasks"], 34)
        self.assertEqual(summary["baseline_accuracy"], "28/34")
        self.assertEqual(summary["objective_accuracy"], "31/34")
        self.assertEqual(summary["guarded_accuracy"], "28/34")
        self.assertEqual(summary["objective_switch_tasks"], ["task_114", "task_59", "task_108", "task_250"])
        self.assertEqual(summary["guarded_switch_tasks"], [])
        self.assertEqual(summary["promptnode_graph_evidence_rows"], "0/34")
        self.assertEqual(summary["strong_router_contract_rows"], "0/34")
        self.assertTrue(summary["blocks_all_objective_switches"])
        self.assertFalse(summary["update2_evidence_ready"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["claim_boundary"],
            "guarded replay over existing traces; no new API or accuracy improvement claim",
        )


if __name__ == "__main__":
    unittest.main()
