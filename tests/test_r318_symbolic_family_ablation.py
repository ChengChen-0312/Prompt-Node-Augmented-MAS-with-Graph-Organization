import unittest


class TestR318SymbolicFamilyAblation(unittest.TestCase):
    def test_nonmath_only_ablation_loses_symbolic_repairs(self):
        from experiment.mmlu.r318_symbolic_family_ablation import build_symbolic_ablation_summary

        rows, summary = build_symbolic_ablation_summary()

        self.assertEqual(summary["run_id"], "R318")
        self.assertEqual(summary["arg_main"], "88/97")
        self.assertEqual(summary["nonmath_only_main"], "90/97")
        self.assertEqual(summary["full_r306_main"], "95/97")
        self.assertEqual(summary["nonmath_only_fix_harm"], "2/0")
        self.assertEqual(summary["symbolic_family_delta"], 5)
        self.assertEqual(summary["removed_component"], "symbolic_verifier_family")
        self.assertFalse(summary["training_authorized_next"])
        self.assertGreater(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
