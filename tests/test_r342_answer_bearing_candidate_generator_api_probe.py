import unittest


class TestR342AnswerBearingCandidateGeneratorApiProbe(unittest.TestCase):
    def test_dry_run_plans_four_verifier_api_calls(self):
        from experiment.mmlu.r342_answer_bearing_candidate_generator_api_probe import build_api_probe_plan

        summary = build_api_probe_plan()

        self.assertEqual(summary["run_id"], "R342")
        self.assertEqual(summary["records"], 4)
        self.assertEqual(summary["api_calls_planned"], 4)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["api_executed"])
        self.assertEqual(summary["next_required_run"], "R342_execute_with_api_or_R343_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
