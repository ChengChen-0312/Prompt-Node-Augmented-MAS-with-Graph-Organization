import unittest


class TestR319AblationTableUpdate(unittest.TestCase):
    def test_all_priority_ablations_are_completed_after_r316_r318(self):
        from experiment.mmlu.r319_ablation_table_update import build_updated_ablation_summary

        summary = build_updated_ablation_summary()
        rows = {row["name"]: row for row in summary["ablation_table"]}

        self.assertEqual(summary["run_id"], "R319")
        self.assertEqual(rows["remove_promptedge_text"]["status"], "completed")
        self.assertEqual(rows["remove_promptedge_text"]["observed_main"], "35/40")
        self.assertEqual(rows["remove_promptedge_text"]["fix_harm"], "0/2")
        self.assertEqual(rows["cost_matched_plain_requery"]["status"], "completed")
        self.assertEqual(rows["cost_matched_plain_requery"]["observed_main"], "37/40")
        self.assertEqual(rows["cost_matched_plain_requery"]["fix_harm"], "1/1")
        self.assertEqual(rows["remove_symbolic_verifier_family"]["status"], "completed")
        self.assertEqual(rows["remove_symbolic_verifier_family"]["observed_main"], "90/97")
        self.assertEqual(summary["priority_pending_ablations"], [])
        self.assertFalse(summary["training_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R320_goal_audit_after_ablations")


if __name__ == "__main__":
    unittest.main()
