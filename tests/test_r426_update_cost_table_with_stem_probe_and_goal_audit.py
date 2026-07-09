import unittest


class TestR426UpdateCostTableWithStemProbeAndGoalAudit(unittest.TestCase):
    def test_updated_cost_table_replaces_missing_stem_cost_with_probe_estimate(self):
        from experiment.mmlu.r426_update_cost_table_with_stem_probe_and_goal_audit import build_updated_cost_table

        summary = build_updated_cost_table()

        self.assertEqual(summary["run_id"], "R426")
        rows = {row["id"]: row for row in summary["cost_rows"]}
        self.assertIn("MMLU_STEM_R306_probe_estimate", rows)
        self.assertEqual(rows["MMLU_STEM_R306_probe_estimate"]["score"], "95/97")
        self.assertAlmostEqual(rows["MMLU_STEM_R306_probe_estimate"]["cost"], 0.676454, places=6)
        self.assertEqual(rows["MMLU_STEM_R306_probe_estimate"]["cost_evidence"], "probe_estimate_not_exact")
        self.assertNotIn("MMLU_STEM_cost_missing", summary["missing_cost_evidence"])
        self.assertIn("independent_integrity_audit_missing", summary["missing_cost_evidence"])
        self.assertFalse(summary["cost_table_complete_for_submission"])
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R422", "R423", "R424", "R425", "R426"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertEqual(summary["next_required_run"], "R427_external_integrity_audit_refresh")


if __name__ == "__main__":
    unittest.main()
