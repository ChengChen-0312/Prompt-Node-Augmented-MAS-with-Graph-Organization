import unittest


class TestR365WrongForwardAndMissedFixAnalysis(unittest.TestCase):
    def test_analysis_identifies_wrong_forward_and_missed_fix_subject_clusters(self):
        from experiment.mmlu.r365_wrong_forward_and_missed_fix_analysis import build_error_analysis

        summary = build_error_analysis()

        self.assertEqual(summary["run_id"], "R365")
        self.assertEqual(summary["wrong_forward_count"], 1)
        self.assertEqual(summary["wrong_forward_task_ids"], ["MMLU-college_mathematics_test-15"])
        self.assertEqual(summary["missed_fix_count"], 10)
        self.assertEqual(summary["missed_fix_subject_counts"]["college_chemistry"], 4)
        self.assertEqual(summary["missed_fix_subject_counts"]["high_school_us_history"], 2)
        self.assertIn("candidate_quality_not_gate_threshold_is_primary_bottleneck", summary["root_causes"])
        self.assertIn("chemistry_and_physics_specialized_verifiers_missing", summary["root_causes"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R366_goal_audit_after_source_invariant_fresh_eval")


if __name__ == "__main__":
    unittest.main()
