import unittest


class BadExactGateForcedMiniSetTests(unittest.TestCase):
    def test_bad_exact_gate_improves_current_forced_template_miniset_without_harm(self):
        from experiment.aqua.bad_exact_gate_forced_miniset_report import build_forced_miniset_summary

        summary = build_forced_miniset_summary()

        self.assertEqual(summary["rule"], "r091_bad_exact_gate_forced_miniset")
        self.assertEqual(summary["num_tasks"], 5)
        self.assertEqual(summary["baseline_solved"], 3)
        self.assertEqual(summary["forced_template_solved"], 4)
        self.assertEqual(summary["gate_solved"], 4)
        self.assertEqual(summary["gate_fix_harm"], {"fix": 1, "harm": 0})
        self.assertEqual(sorted(summary["accepted_tasks"]), ["task_108", "task_188", "task_8"])
        self.assertEqual(sorted(summary["fallback_tasks"]), ["task_114", "task_56"])
        self.assertAlmostEqual(summary["total_forced_template_cost"], 0.20125, places=6)
        self.assertEqual(summary["decision_field_violations"], 0)
        self.assertEqual(summary["claim_boundary"], "five-task forced-template mini-set, not tail34 accuracy")


if __name__ == "__main__":
    unittest.main()
