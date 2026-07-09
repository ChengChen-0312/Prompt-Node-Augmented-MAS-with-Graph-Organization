import unittest


class TestR336ProspectiveSelectorEvalSmokeAnalysis(unittest.TestCase):
    def test_smoke_analysis_allows_expansion_only_as_no_harm_not_improvement(self):
        from experiment.mmlu.r336_prospective_selector_eval_smoke_analysis import build_smoke_analysis

        summary = build_smoke_analysis()

        self.assertEqual(summary["run_id"], "R336")
        self.assertEqual(summary["selector_vs_arg"]["delta_correct"], 0)
        self.assertEqual(summary["selector_vs_arg"]["fix_harm"], "0/0")
        self.assertTrue(summary["claim_permissions"]["selector_no_harm_smoke_allowed"])
        self.assertFalse(summary["claim_permissions"]["selector_improvement_claim_allowed"])
        self.assertTrue(summary["claim_permissions"]["plain_requery_harm_control_allowed"])
        self.assertTrue(summary["expand_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R337_prospective_selector_eval_expand24")


if __name__ == "__main__":
    unittest.main()
