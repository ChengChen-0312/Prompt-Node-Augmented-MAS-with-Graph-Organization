import unittest


class ForcedTemplateGateR058StressTests(unittest.TestCase):
    def test_r086_gate_does_not_generalize_to_dense_r058_candidates(self):
        from experiment.aqua.forced_template_gate_r058_stress import build_r058_stress_summary

        summary = build_r058_stress_summary()

        self.assertEqual(summary["rule"], "r087_r086_gate_on_r058_stress")
        self.assertEqual(summary["num_tasks"], 34)
        self.assertEqual(summary["baseline_solved"], 28)
        self.assertEqual(summary["dense_promptnode_solved"], 25)
        self.assertEqual(summary["gate_solved"], 26)
        self.assertEqual(summary["gate_fix_harm"], {"fix": 1, "harm": 3})
        self.assertEqual(summary["decision_field_violations"], 0)
        self.assertEqual(summary["claim_boundary"], "r058 stress replay, not a new accuracy method")


if __name__ == "__main__":
    unittest.main()
