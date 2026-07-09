import unittest


class BadExactGateTask108SmokeTests(unittest.TestCase):
    def test_task108_fresh_forced_template_smoke_is_accepted_by_bad_exact_gate(self):
        from experiment.aqua.bad_exact_gate_task108_smoke_report import build_task108_smoke_summary

        summary = build_task108_smoke_summary()

        self.assertEqual(summary["rule"], "r090_task108_forced_template_bad_exact_gate_smoke")
        self.assertEqual(summary["task_id"], "task_108")
        self.assertEqual(summary["baseline_solved"], 0)
        self.assertEqual(summary["forced_template_solved"], 1)
        self.assertEqual(summary["gate_solved"], 1)
        self.assertEqual(summary["gate_action"], "accept_template")
        self.assertEqual(summary["gate_reason"], "trusted_exact_contract")
        self.assertEqual(summary["decision_field_violations"], 0)
        self.assertEqual(summary["claim_boundary"], "single-task fresh smoke, not tail34 accuracy")


if __name__ == "__main__":
    unittest.main()
