import unittest


class TestR425AnalyzeMmluStemCostProbe(unittest.TestCase):
    def test_probe_analysis_extrapolates_main97_cost_as_estimate(self):
        from experiment.mmlu.r425_analyze_mmlu_stem_cost_probe import build_cost_probe_analysis

        summary = build_cost_probe_analysis()

        self.assertEqual(summary["run_id"], "R425")
        self.assertEqual(summary["cost_probe_tasks"], 12)
        self.assertEqual(summary["api_errors"], 0)
        self.assertEqual(summary["estimate_kind"], "probe_extrapolated")
        self.assertGreater(summary["estimated_main97_combined_cost"], 0)
        self.assertEqual(summary["mmlu_stem_cost_gap_status"], "resolved_as_estimate_not_exact")
        self.assertFalse(summary["accuracy_claim_from_probe_authorized"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R426_update_cost_table_with_stem_probe_and_goal_audit")


if __name__ == "__main__":
    unittest.main()
