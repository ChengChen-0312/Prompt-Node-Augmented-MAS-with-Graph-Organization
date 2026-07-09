import unittest


class ObjectiveSafetyProxyRegressionStressTests(unittest.TestCase):
    def test_proxy_reproduces_rank5_guard_on_clean_harm_and_recovery_cases(self):
        from experiment.aqua.objective_safety_proxy_regression_stress import (
            build_proxy_regression_stress_summary,
        )

        summary = build_proxy_regression_stress_summary()

        self.assertEqual(summary["rule"], "r114_objective_safety_proxy_regression_stress")
        self.assertEqual(summary["learned_rule"], "diff_and_top_score_ge_3_or_split")
        self.assertEqual(summary["num_tasks"], 4)
        self.assertEqual(summary["proxy_action_agreement_with_r107"], "4/4")
        self.assertEqual(summary["baseline_solved"], 2)
        self.assertEqual(summary["rank5_solved"], 3)
        self.assertEqual(summary["proxy_guarded_solved"], 4)
        self.assertEqual(summary["proxy_switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["proxy_fallback_tasks"], ["task_8", "task_188"])
        self.assertEqual(summary["suppressed_rank5_harm_tasks"], ["task_8"])
        self.assertEqual(summary["clean_recovery_tasks"], ["task_250"])
        self.assertEqual(summary["proxy_fix_harm"], "2/0")
        self.assertEqual(summary["proxy_clean_fix_harm"], "1/0")
        self.assertEqual(summary["proxy_noisy_fix_harm"], "1/0")
        self.assertEqual(summary["proxy_input_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "four-task regression replay of R113 over R106/R107 traces; no new API or held-out accuracy claim",
        )


if __name__ == "__main__":
    unittest.main()
