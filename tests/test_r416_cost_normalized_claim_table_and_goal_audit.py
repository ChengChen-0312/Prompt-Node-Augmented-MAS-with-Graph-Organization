import unittest


class TestR416CostNormalizedClaimTableAndGoalAudit(unittest.TestCase):
    def test_cost_table_records_available_costs_and_submission_gaps(self):
        from experiment.mmlu.r416_cost_normalized_claim_table_and_goal_audit import build_cost_table

        summary = build_cost_table()

        self.assertEqual(summary["run_id"], "R416")
        rows = {row["id"]: row for row in summary["cost_rows"]}
        self.assertIn("AQuA_R068_cost_reduced", rows)
        self.assertIn("MMLU_DefinitionChallenge_R413", rows)
        self.assertIn("MMLU_plain_requery_R316", rows)
        self.assertEqual(rows["MMLU_DefinitionChallenge_R413"]["score"], "22/24")
        self.assertAlmostEqual(rows["MMLU_DefinitionChallenge_R413"]["cost"], 0.220095, places=6)
        self.assertEqual(rows["MMLU_DefinitionChallenge_R413"]["fix_harm_wrong"], "1/0/0")

        self.assertFalse(summary["cost_table_complete_for_submission"])
        self.assertIn("MMLU_STEM_cost_missing", summary["missing_cost_evidence"])
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R412", "R413", "R414", "R415", "R416"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["cost_reporting_gap_visible"])
        self.assertEqual(summary["next_required_run"], "R417_case_study_evidence_pack")


if __name__ == "__main__":
    unittest.main()
