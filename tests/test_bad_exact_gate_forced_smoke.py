import unittest


class BadExactGateForcedSmokeTests(unittest.TestCase):
    def test_bad_exact_gate_preserves_forced_template_smoke_without_harm(self):
        from experiment.aqua.bad_exact_gate_forced_smoke import build_forced_smoke_gate_summary

        summary = build_forced_smoke_gate_summary()

        self.assertEqual(summary["rule"], "r089_bad_exact_gate_forced_smoke_replay")
        self.assertEqual(summary["num_smoke_rows"], 4)
        self.assertEqual(summary["baseline_solved"], 3)
        self.assertEqual(summary["forced_template_solved"], 3)
        self.assertEqual(summary["gate_solved"], 3)
        self.assertEqual(summary["gate_fix_harm"], {"fix": 0, "harm": 0})
        self.assertEqual(summary["accepted_rows"], 2)
        self.assertEqual(summary["fallback_rows"], 2)
        self.assertEqual(sorted(summary["accepted_tasks"]), ["task_188", "task_8"])
        self.assertEqual(sorted(summary["fallback_tasks"]), ["task_114", "task_56"])
        self.assertEqual(summary["decision_field_violations"], 0)
        self.assertEqual(summary["claim_boundary"], "forced-template smoke replay, not tail34 accuracy")


if __name__ == "__main__":
    unittest.main()
