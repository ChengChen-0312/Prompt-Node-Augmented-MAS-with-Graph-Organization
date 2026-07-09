import unittest


class TestR411CurriculumGateAblationAndGoalAudit(unittest.TestCase):
    def test_ablation_finds_diagnostic_gate_but_blocks_claim_and_checks_goal(self):
        from experiment.mmlu.r411_curriculum_gate_ablation_and_goal_audit import build_gate_ablation

        summary = build_gate_ablation()

        self.assertEqual(summary["run_id"], "R411")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R407", "R408", "R409", "R410", "R411"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["overclaiming_blocked"])

        ablations = {row["name"]: row for row in summary["gate_ablations"]}
        self.assertIn("parser_repair_conservative", ablations)
        self.assertIn("relaxed_margin_015", ablations)
        self.assertIn("logical_fallacy_definition_gate", ablations)
        self.assertEqual(summary["best_diagnostic_gate"]["name"], "logical_fallacy_definition_gate")
        self.assertEqual(summary["best_diagnostic_gate"]["hybrid_correct"], 28)
        self.assertEqual(summary["best_diagnostic_gate"]["fixes"], 1)
        self.assertEqual(summary["best_diagnostic_gate"]["harms"], 0)
        self.assertTrue(summary["same_split_diagnostic_only"])

        self.assertFalse(summary["claim_permissions"]["positive_nonmath_claim_allowed"])
        self.assertTrue(summary["claim_permissions"]["fresh_prospective_gate_preflight_allowed_next"])
        self.assertEqual(summary["next_required_run"], "R412_fresh_definition_challenge_gate_preflight")


if __name__ == "__main__":
    unittest.main()
