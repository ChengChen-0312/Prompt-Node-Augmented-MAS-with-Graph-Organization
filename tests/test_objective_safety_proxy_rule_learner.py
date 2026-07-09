import unittest


class ObjectiveSafetyProxyRuleLearnerTests(unittest.TestCase):
    def test_learns_first200_rule_and_evaluates_on_frozen_tail34_targets(self):
        from experiment.aqua.objective_safety_proxy_rule_learner import build_proxy_rule_summary

        summary = build_proxy_rule_summary()

        self.assertEqual(summary["rule"], "r113_objective_safety_proxy_rule_learner")
        self.assertEqual(summary["train_rows"], 200)
        self.assertEqual(summary["frozen_eval_rows"], 34)
        self.assertEqual(summary["learned_rule"], "diff_and_top_score_ge_3_or_split")
        self.assertEqual(summary["train_target_agreement"], "200/200")
        self.assertEqual(summary["frozen_tail34_target_agreement"], "34/34")
        self.assertEqual(summary["frozen_tail34_switch_tasks"], ["task_108", "task_250"])
        self.assertFalse(summary["uses_tail34_training_source"])
        self.assertEqual(summary["proxy_input_field_violations"], 0)
        self.assertEqual(summary["candidate_rule_count"], 16)
        self.assertEqual(
            summary["claim_boundary"],
            "rule-proxy target agreement only; no answer accuracy or prospective API claim",
        )


if __name__ == "__main__":
    unittest.main()
