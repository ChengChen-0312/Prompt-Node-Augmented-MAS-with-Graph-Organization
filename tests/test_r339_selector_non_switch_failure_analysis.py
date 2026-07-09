import unittest


class TestR339SelectorNonSwitchFailureAnalysis(unittest.TestCase):
    def test_failure_analysis_identifies_missing_answer_bearing_candidates(self):
        from experiment.mmlu.r339_selector_non_switch_failure_analysis import build_non_switch_analysis

        summary = build_non_switch_analysis()

        self.assertEqual(summary["run_id"], "R339")
        self.assertEqual(summary["selector_action_counts"], {"KEEP_ARG": 24})
        self.assertEqual(summary["selector_switches"], 0)
        self.assertEqual(summary["baseline_wrong_tasks"], 4)
        self.assertEqual(summary["selector_wrong_tasks"], 4)
        self.assertEqual(summary["answer_bearing_candidate_count"], 0)
        self.assertIn("no_answer_bearing_candidates", summary["root_causes"])
        self.assertIn("over_conservative_switch_contract", summary["root_causes"])
        self.assertEqual(summary["next_required_run"], "R340_answer_bearing_candidate_generator_design")


if __name__ == "__main__":
    unittest.main()
