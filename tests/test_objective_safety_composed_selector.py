import unittest


class ObjectiveSafetyComposedSelectorTests(unittest.TestCase):
    def test_safety_composed_objective_selector_keeps_clean_fix_without_harm(self):
        from experiment.aqua.objective_safety_composed_selector import (
            build_objective_safety_summary,
        )

        summary = build_objective_safety_summary()

        self.assertEqual(summary["rule"], "r095_objective_safety_composed_selector")
        self.assertEqual(summary["num_tasks"], 34)
        self.assertEqual(summary["baseline_solved"], 28)
        self.assertEqual(summary["objective_selector_solved"], 31)
        self.assertEqual(summary["safety_composed_solved"], 30)
        self.assertEqual(summary["safety_composed_fix_harm"], {"fix": 2, "harm": 0})
        self.assertEqual(sorted(summary["accepted_switch_tasks"]), ["task_108", "task_250"])
        self.assertEqual(sorted(summary["suppressed_switch_tasks"]), ["task_114", "task_59"])
        self.assertEqual(summary["by_clean_label"]["clean"]["gate_solved"], 28)
        self.assertEqual(summary["by_clean_label"]["clean"]["fix_harm"], {"fix": 1, "harm": 0})
        self.assertEqual(summary["by_clean_label"]["clean"]["fix_tasks"], ["task_250"])
        self.assertEqual(summary["by_clean_label"]["noisy"]["gate_solved"], 2)
        self.assertEqual(summary["by_clean_label"]["noisy"]["fix_harm"], {"fix": 1, "harm": 0})
        self.assertEqual(summary["by_clean_label"]["noisy"]["fix_tasks"], ["task_108"])
        self.assertEqual(summary["decision_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "label-free replay over R065 multi-view traces; not an explicit forced-template or transfer result",
        )


if __name__ == "__main__":
    unittest.main()
