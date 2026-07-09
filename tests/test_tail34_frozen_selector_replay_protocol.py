import unittest


class Tail34FrozenSelectorReplayProtocolTests(unittest.TestCase):
    def test_replay_combines_r059_baseline_with_r146_switches(self):
        from experiment.aqua.tail34_frozen_selector_replay_protocol import (
            build_tail34_frozen_selector_replay_summary,
        )

        summary = build_tail34_frozen_selector_replay_summary()

        self.assertEqual(
            summary["rule"],
            "r147_tail34_frozen_selector_replay_and_expansion_protocol",
        )
        self.assertTrue(summary["full_tail34_replay_only"])
        self.assertTrue(summary["no_new_api_run"])
        self.assertEqual(summary["total_tasks"], 34)
        self.assertEqual(summary["baseline_accuracy"], "28/34")
        self.assertEqual(summary["selected_accuracy"], "30/34")
        self.assertEqual(summary["switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["fallback_task_count"], 32)
        self.assertEqual(summary["fix_harm"], "2/0")
        self.assertEqual(summary["clean_fix_harm"], "1/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(summary["promptnode_graph_evidence_on_switches"], "2/2")
        self.assertEqual(summary["selector_input_field_violations"], 0)
        self.assertFalse(summary["uses_tail34_training_source"])
        self.assertAlmostEqual(summary["baseline_cost"], 0.93285, places=6)
        self.assertAlmostEqual(summary["incremental_promptnode_cost"], 0.07071, places=6)
        self.assertAlmostEqual(summary["selected_estimated_cost"], 1.00356, places=6)
        self.assertFalse(summary["fresh_integrated_full_run"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "r148_tail34_replay_statistical_audit_and_transfer_preflight",
        )


if __name__ == "__main__":
    unittest.main()
