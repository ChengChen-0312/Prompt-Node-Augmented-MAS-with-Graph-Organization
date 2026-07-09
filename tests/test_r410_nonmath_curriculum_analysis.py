import unittest


class TestR410NonmathCurriculumAnalysis(unittest.TestCase):
    def test_analysis_separates_candidate_signal_parser_bug_and_gate_limit(self):
        from experiment.mmlu.r410_nonmath_curriculum_analysis import build_curriculum_analysis

        summary = build_curriculum_analysis()

        self.assertEqual(summary["run_id"], "R410")
        self.assertEqual(summary["records"], 32)
        self.assertEqual(summary["arg_correct"], 27)
        self.assertEqual(summary["hybrid_correct"], 27)
        self.assertEqual(summary["candidate_correct"], 28)
        self.assertEqual(summary["candidate_oracle_delta"], 1)
        self.assertEqual(summary["candidate_oracle_fixes"], 2)
        self.assertEqual(summary["candidate_oracle_harms"], 1)

        self.assertGreater(summary["parser_repair"]["label_but_zero_node_fields"], 0)
        self.assertEqual(summary["parser_repair_replay"]["hybrid_correct"], 27)
        self.assertEqual(summary["parser_repair_replay"]["fixes"], 0)
        self.assertEqual(summary["parser_repair_replay"]["harms"], 0)

        self.assertFalse(summary["claim_permissions"]["positive_nonmath_claim_allowed"])
        self.assertTrue(summary["claim_permissions"]["parser_repair_required"])
        self.assertTrue(summary["claim_permissions"]["learned_gate_ablation_allowed_next"])
        self.assertEqual(summary["next_required_run"], "R411_curriculum_gate_ablation_and_goal_audit")


if __name__ == "__main__":
    unittest.main()
