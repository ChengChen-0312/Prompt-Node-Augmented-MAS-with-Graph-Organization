import unittest


class TestR321PaperEvidenceTableAndTrainingGate(unittest.TestCase):
    def test_paper_table_preserves_positive_results_and_nonstem_boundary(self):
        from experiment.mmlu.r321_paper_evidence_table_and_training_gate import build_paper_evidence_summary

        summary = build_paper_evidence_summary()
        rows = {row["slice"]: row for row in summary["paper_main_results"]}
        gate = summary["selector_training_gate"]

        self.assertEqual(summary["run_id"], "R321")
        self.assertEqual(rows["AQuA_audit_clean_tail31"]["baseline"], "28/31")
        self.assertEqual(rows["AQuA_audit_clean_tail31"]["promptnode"], "31/31")
        self.assertEqual(rows["MMLU_STEM_main97"]["baseline"], "88/97")
        self.assertEqual(rows["MMLU_STEM_main97"]["promptnode"], "95/97")
        self.assertEqual(rows["MMLU_nonSTEM40_safety_replay"]["baseline"], "37/40")
        self.assertEqual(rows["MMLU_nonSTEM40_safety_replay"]["promptnode"], "37/40")
        self.assertEqual(rows["MMLU_nonSTEM40_safety_replay"]["paper_claim"], "no_harm_boundary_only")
        self.assertEqual(summary["ablation_summary"]["completed_count"], 10)
        self.assertEqual(summary["ablation_summary"]["priority_pending"], [])
        self.assertTrue(gate["preflight_authorized"])
        self.assertFalse(gate["execute_training_authorized"])
        self.assertIn("warning_only_promptnode_override", gate["forbidden_training_signals"])
        self.assertIn("promptedge_text_features", gate["required_features"])
        self.assertEqual(summary["next_required_run"], "R322_selector_training_preflight")


if __name__ == "__main__":
    unittest.main()
