import unittest


class MMLUBoundedCheckpointBuildExecutionReportTests(unittest.TestCase):
    def test_r161_report_parses_completed_checkpoint_build_without_overclaiming(self):
        from experiment.mmlu.bounded_checkpoint_build_execution_report import (
            build_execution_summary,
        )

        summary = build_execution_summary()

        self.assertEqual(summary["rule"], "r161_bounded_mmlu_checkpoint_build_execution")
        self.assertTrue(summary["bounded_build_run"])
        self.assertTrue(summary["pipeline_complete"])
        self.assertTrue(summary["checkpoint_training_run"])
        self.assertTrue(summary["compatible_checkpoint_exists"])
        self.assertFalse(summary["transfer_result"])
        self.assertFalse(summary["downstream_accuracy_claim_supported"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["errors_detected"], [])
        self.assertTrue(summary["transfer_eval_allowed_next"])
        self.assertEqual(summary["llm_name"], "gpt-4o-2024-08-06")
        self.assertEqual(summary["num_iterations"], 10)
        self.assertEqual(summary["batch_size"], 4)
        self.assertEqual(summary["cold_start_graph_count"], 92)
        self.assertEqual(summary["finetune_graph_count"], 311)
        self.assertEqual(summary["stage2a_pruned_graphs_saved"], 23)
        self.assertEqual(summary["stage2c_replay_graphs_copied"], 27)
        self.assertEqual(len(summary["simple_topology_results"]), 12)
        self.assertEqual(summary["best_simple_topology"]["config"], "Layered-4")
        self.assertEqual(summary["best_simple_topology"]["correct"], 23)
        self.assertEqual(summary["stage1"]["best_epoch"], 6)
        self.assertAlmostEqual(summary["stage1"]["best_validation_loss"], 2.7816)
        self.assertEqual(summary["stage3"]["best_epoch"], 95)
        self.assertAlmostEqual(summary["stage3"]["best_validation_loss"], 2.6520)
        self.assertEqual(summary["stage3"]["final_epoch"], 100)
        self.assertAlmostEqual(summary["stage3"]["final_validation_loss"], 2.6830)
        self.assertEqual(summary["next_protocol"], "r162_mmlu_transfer_eval_preflight_or_bounded_eval")
        self.assertEqual(summary["next_goal_audit_due"], "R165")


if __name__ == "__main__":
    unittest.main()
