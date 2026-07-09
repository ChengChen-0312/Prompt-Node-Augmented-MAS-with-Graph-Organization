import unittest


class ObjectiveSafetyTemplatePlanReplayTests(unittest.TestCase):
    def test_r097_rank1_template_plan_does_not_reproduce_clean_r095_switch(self):
        from experiment.aqua.objective_safety_template_plan_replay import build_template_plan_replay_summary

        summary = build_template_plan_replay_summary()

        self.assertEqual(summary["rule"], "r098_template_plan_replay_on_r092")
        self.assertEqual(summary["num_tasks"], 34)
        self.assertEqual(summary["arg_baseline_solved"], 28)
        self.assertEqual(summary["template_plan_replay_solved"], 29)
        self.assertEqual(summary["switch_plan_count"], 2)
        self.assertEqual(summary["forced_result_available_for_switches"], 2)
        self.assertEqual(summary["desired_prediction_match_count"], 1)
        self.assertEqual(summary["desired_prediction_mismatch_tasks"], ["task_250"])
        self.assertEqual(summary["clean_desired_prediction_match_tasks"], [])
        self.assertEqual(summary["noisy_desired_prediction_match_tasks"], ["task_108"])
        self.assertEqual(summary["fix_harm"], "1/0")
        self.assertEqual(summary["clean_fix_harm"], "0/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        self.assertEqual(
            summary["claim_boundary"],
            "R097 plan replay over R092 forced-template results; no new API; not R095 reproduction",
        )


if __name__ == "__main__":
    unittest.main()
