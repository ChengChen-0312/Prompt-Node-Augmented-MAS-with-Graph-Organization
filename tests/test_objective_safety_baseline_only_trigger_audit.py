import unittest


class ObjectiveSafetyBaselineOnlyTriggerAuditTests(unittest.TestCase):
    def test_baseline_only_trigger_cannot_replace_objective_trace(self):
        from experiment.aqua.objective_safety_baseline_only_trigger_audit import (
            build_baseline_only_trigger_audit_summary,
        )

        summary = build_baseline_only_trigger_audit_summary()

        self.assertEqual(summary["rule"], "r116_objective_safety_baseline_only_trigger_audit")
        self.assertEqual(summary["candidate_rule_count"], 6)
        self.assertEqual(summary["best_train_rule"], "always_fallback")
        self.assertEqual(summary["best_train_agreement"], "189/200")
        self.assertEqual(summary["best_train_frozen_tail34_agreement"], "32/34")
        self.assertEqual(summary["best_train_frozen_switch_recall"], "0/2")
        self.assertEqual(summary["baseline_split_frozen_switch_recall"], "1/2")
        self.assertEqual(summary["baseline_split_false_switch_tasks"], ["task_6"])
        self.assertEqual(summary["baseline_split_missed_switch_tasks"], ["task_250"])
        self.assertEqual(summary["best_recall_rule"], "baseline_direct_valid_ge2")
        self.assertEqual(summary["best_recall_frozen_switch_recall"], "2/2")
        self.assertEqual(summary["best_recall_frozen_switch_precision"], "2/26")
        self.assertEqual(summary["best_recall_frozen_tail34_agreement"], "10/34")
        self.assertFalse(summary["baseline_only_proxy_sufficient"])
        self.assertEqual(summary["input_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "baseline-only trigger audit; no accuracy, cost-reduction, or deployment claim",
        )


if __name__ == "__main__":
    unittest.main()
