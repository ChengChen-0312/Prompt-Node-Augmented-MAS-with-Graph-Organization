import unittest


class TestR400ContrastiveVerifierTargetedApiExecution(unittest.TestCase):
    def test_api_execution_plan_is_leakage_checked(self):
        from experiment.mmlu.r400_contrastive_verifier_targeted_api_execution import build_api_execution_plan

        summary = build_api_execution_plan()

        self.assertEqual(summary["run_id"], "R400")
        self.assertEqual(summary["records"], 7)
        self.assertEqual(summary["api_calls_planned"], 7)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["api_executed"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R400_execute_with_api_or_R401_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
