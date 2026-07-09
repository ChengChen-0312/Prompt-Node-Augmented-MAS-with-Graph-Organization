import unittest


class TestR343AnswerBearingCandidateProbeAnalysis(unittest.TestCase):
    def test_probe_analysis_blocks_same_prompt_only_verifier_expansion(self):
        from experiment.mmlu.r343_answer_bearing_candidate_probe_analysis import build_probe_failure_analysis

        summary = build_probe_failure_analysis()

        self.assertEqual(summary["run_id"], "R343")
        self.assertEqual(summary["records"], 4)
        self.assertEqual(summary["api_executed"], 4)
        self.assertEqual(summary["candidate_label_count"], 4)
        self.assertEqual(summary["candidate_correct_count"], 0)
        self.assertEqual(summary["candidate_repairs_baseline_count"], 0)
        self.assertEqual(summary["candidate_follows_wrong_baseline_count"], 4)
        self.assertIn("verifier_candidates_follow_wrong_baseline", summary["root_causes"])
        self.assertIn("prompt_only_answer_verifiers_not_sufficient", summary["root_causes"])
        self.assertIn("requires_executable_or_symbolic_verification", summary["course_correction"])
        self.assertFalse(summary["claim_permissions"]["answer_bearing_generator_improvement_claim_allowed"])
        self.assertFalse(summary["claim_permissions"]["more_api_same_design_allowed"])
        self.assertTrue(summary["claim_permissions"]["tool_verifier_design_required"])
        self.assertEqual(summary["next_required_run"], "R344_goal_audit_after_candidate_generator_probe")


if __name__ == "__main__":
    unittest.main()
