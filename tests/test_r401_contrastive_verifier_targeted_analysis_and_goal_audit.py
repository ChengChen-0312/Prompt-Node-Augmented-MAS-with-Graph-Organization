import unittest


class TestR401ContrastiveVerifierTargetedAnalysisAndGoalAudit(unittest.TestCase):
    def test_analysis_blocks_failed_contrastive_path_and_redirects_to_claim_synthesis(self):
        from experiment.mmlu.r401_contrastive_verifier_targeted_analysis_and_goal_audit import build_targeted_analysis

        summary = build_targeted_analysis()

        self.assertEqual(summary["run_id"], "R401")
        self.assertEqual(summary["records"], 7)
        self.assertEqual(summary["candidate_label_count"], 0)
        self.assertEqual(summary["contract_pass_count"], 6)
        self.assertEqual(summary["contract_inconsistency_count"], 6)
        self.assertEqual(summary["candidate_repairs_arg_count"], 0)
        self.assertTrue(summary["goal_alignment"]["contrastive_path_failed_safely"])
        self.assertTrue(summary["goal_alignment"]["overclaiming_blocked"])
        self.assertFalse(summary["claim_permissions"]["integrate_contrastive_path"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R402_result_to_claim_synthesis_for_paper")


if __name__ == "__main__":
    unittest.main()
