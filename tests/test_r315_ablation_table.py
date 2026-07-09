import unittest


class TestR315AblationTable(unittest.TestCase):
    def test_ablation_table_includes_completed_and_pending_reviewer_checks(self):
        from experiment.mmlu.r315_ablation_table import build_ablation_table_summary

        summary = build_ablation_table_summary()
        rows = {row["name"]: row for row in summary["ablation_table"]}

        self.assertEqual(summary["run_id"], "R315")
        self.assertEqual(rows["remove_nonmath_promptnodes"]["status"], "completed")
        self.assertEqual(rows["remove_nonmath_promptnodes"]["reference"], "R306_vs_R304")
        self.assertEqual(rows["remove_safety_gate"]["status"], "completed")
        self.assertEqual(rows["remove_safety_gate"]["observed_main"], "83/97")
        self.assertEqual(rows["remove_lifecycle_prune"]["status"], "completed")
        self.assertEqual(rows["remove_lifecycle_prune"]["observed_main"], "95/97")
        self.assertEqual(rows["remove_lifecycle_prune"]["interpretation"], "accuracy_ties_but_cost_worse")
        self.assertEqual(rows["remove_promptedge_text"]["status"], "pending")
        self.assertEqual(rows["cost_matched_plain_requery"]["status"], "pending")
        self.assertFalse(summary["training_authorized_next"])
        self.assertFalse(summary["sci_q2_ready"])

    def test_ready_to_run_next_prioritizes_config_only_ablations(self):
        from experiment.mmlu.r315_ablation_table import build_ablation_table_summary

        summary = build_ablation_table_summary()

        self.assertEqual(summary["next_required_run"], "R316_promptedge_text_and_cost_matched_controls")
        self.assertIn("remove_promptedge_text", summary["priority_pending_ablations"])
        self.assertIn("cost_matched_plain_requery", summary["priority_pending_ablations"])


if __name__ == "__main__":
    unittest.main()
