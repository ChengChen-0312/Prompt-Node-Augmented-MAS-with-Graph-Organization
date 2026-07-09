import unittest


class ForcedTemplateBaselineSplitGateTests(unittest.TestCase):
    def test_baseline_split_gate_keeps_task108_and_suppresses_clean_harms(self):
        from experiment.aqua.forced_template_baseline_split_gate import (
            build_baseline_split_gate_summary,
        )

        summary = build_baseline_split_gate_summary()

        self.assertEqual(summary["rule"], "r094_baseline_split_protected_forced_template_gate")
        self.assertEqual(summary["num_tasks"], 34)
        self.assertEqual(summary["baseline_solved"], 28)
        self.assertEqual(summary["forced_template_solved"], 25)
        self.assertEqual(summary["r088_gate_solved"], 27)
        self.assertEqual(summary["split_gate_solved"], 29)
        self.assertEqual(summary["split_gate_fix_harm"], {"fix": 1, "harm": 0})
        self.assertEqual(summary["accepted_switch_tasks"], ["task_108"])
        self.assertEqual(sorted(summary["suppressed_switch_tasks"]), ["task_188", "task_8"])
        self.assertEqual(summary["by_clean_label"]["clean"]["gate_solved"], 27)
        self.assertEqual(summary["by_clean_label"]["clean"]["fix_harm"], {"fix": 0, "harm": 0})
        self.assertEqual(summary["by_clean_label"]["noisy"]["gate_solved"], 2)
        self.assertEqual(summary["by_clean_label"]["noisy"]["fix_harm"], {"fix": 1, "harm": 0})
        self.assertEqual(summary["decision_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "label-free replay over R092 traces; official gain is noisy-only, not SCI main result",
        )


if __name__ == "__main__":
    unittest.main()
