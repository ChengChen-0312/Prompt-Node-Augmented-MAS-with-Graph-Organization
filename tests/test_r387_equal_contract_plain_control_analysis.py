import unittest


class TestR387EqualContractPlainControlAnalysis(unittest.TestCase):
    def test_analysis_shows_promptedge_binding_survives_equal_contract_control(self):
        from experiment.mmlu.r387_equal_contract_plain_control_analysis import build_equal_contract_analysis

        summary = build_equal_contract_analysis()

        self.assertEqual(summary["run_id"], "R387")
        self.assertEqual(summary["records"], 24)
        self.assertEqual(summary["arg_correct"], 21)
        self.assertEqual(summary["option_binding_correct"], 24)
        self.assertEqual(summary["equal_contract_strict_correct"], 10)
        self.assertEqual(summary["equal_contract_explicit_fallback_correct"], 16)
        self.assertEqual(summary["equal_contract_empty_label_count"], 14)
        self.assertGreater(summary["option_binding_delta_vs_equal_contract_fallback"], 0)
        self.assertTrue(summary["claim_permissions"]["same_task_control_survived"])
        self.assertFalse(summary["claim_permissions"]["main_paper_claim_allowed"])
        self.assertEqual(summary["next_required_run"], "R388_mixed_nonmath_option_binding_preflight")


if __name__ == "__main__":
    unittest.main()
