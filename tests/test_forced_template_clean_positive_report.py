import unittest


class ForcedTemplateCleanPositiveReportTests(unittest.TestCase):
    def test_clean_positive_smoke_summary_keeps_claim_boundary(self):
        from experiment.aqua.forced_template_clean_positive_report import build_clean_positive_summary

        summary = build_clean_positive_summary()

        self.assertEqual(summary["rule"], "r085_forced_template_clean_positive_smoke")
        self.assertEqual(summary["clean_positive_runs"], 3)
        self.assertEqual(summary["clean_positive_solved"], 3)
        self.assertEqual(summary["boundary_runs"], 1)
        self.assertEqual(summary["boundary_solved"], 0)
        self.assertEqual(summary["claim_boundary"], "clean-positive smoke only, not tail34 accuracy")


if __name__ == "__main__":
    unittest.main()
