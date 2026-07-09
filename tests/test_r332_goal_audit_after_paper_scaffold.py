import unittest


class TestR332GoalAuditAfterPaperScaffold(unittest.TestCase):
    def test_goal_audit_redirects_from_writing_back_to_prospective_evaluation(self):
        from experiment.mmlu.r332_goal_audit_after_paper_scaffold import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["run_id"], "R332")
        self.assertEqual(summary["iterations_since_last_goal_check"], ["R327", "R328", "R329", "R330", "R331"])
        self.assertTrue(summary["goal_alignment"]["still_aligned_with_sci_q2_goal"])
        self.assertTrue(summary["goal_alignment"]["paper_scaffold_created"])
        self.assertTrue(summary["goal_alignment"]["selector_claim_not_overstated"])
        self.assertTrue(summary["goal_alignment"]["case_studies_ready"])
        self.assertFalse(summary["claim_permissions"]["broad_general_promptnode_claim_allowed"])
        self.assertFalse(summary["claim_permissions"]["sci_q2_ready"])
        self.assertEqual(summary["course_correction"][0], "Prioritize prospective selector evaluation before drafting full paper prose.")
        self.assertEqual(summary["next_required_run"], "R333_prospective_selector_eval_design")


if __name__ == "__main__":
    unittest.main()
