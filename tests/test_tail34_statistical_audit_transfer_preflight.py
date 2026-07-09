import unittest


class Tail34StatisticalAuditTransferPreflightTests(unittest.TestCase):
    def test_audit_reports_nonsignificant_replay_and_transfer_blocker(self):
        from experiment.aqua.tail34_statistical_audit_transfer_preflight import (
            build_tail34_statistical_audit_transfer_preflight_summary,
        )

        summary = build_tail34_statistical_audit_transfer_preflight_summary()

        self.assertEqual(
            summary["rule"],
            "r148_tail34_replay_statistical_audit_and_transfer_preflight",
        )
        self.assertEqual(summary["baseline_accuracy"], "28/34")
        self.assertEqual(summary["selected_accuracy"], "30/34")
        self.assertEqual(summary["paired_improvements"], 2)
        self.assertEqual(summary["paired_regressions"], 0)
        self.assertAlmostEqual(summary["accuracy_delta"], 0.058824, places=6)
        self.assertAlmostEqual(summary["mcnemar_exact_p_two_sided"], 0.5, places=6)
        self.assertFalse(summary["statistically_significant_at_0_05"])
        self.assertFalse(summary["cost_normalized_superiority_supported"])
        self.assertTrue(summary["mmlu_transfer_jsonl_exists"])
        self.assertEqual(summary["mmlu_transfer_rows"], 100)
        self.assertTrue(summary["mmlu_task_split_exists"])
        self.assertTrue(summary["mmlu_evaluator_exists"])
        self.assertFalse(summary["mmlu_arg_checkpoint_available"])
        self.assertFalse(summary["transfer_api_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "r149_transfer_checkpoint_or_aqua_replicate_protocol",
        )


if __name__ == "__main__":
    unittest.main()
