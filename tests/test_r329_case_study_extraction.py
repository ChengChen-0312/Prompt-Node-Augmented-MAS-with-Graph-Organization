import unittest


class TestR329CaseStudyExtraction(unittest.TestCase):
    def test_case_studies_cover_required_promptnode_mechanisms(self):
        from experiment.mmlu.r329_case_study_extraction import build_case_study_summary

        summary = build_case_study_summary()
        mechanisms = {case["mechanism"] for case in summary["case_studies"]}

        self.assertEqual(summary["run_id"], "R329")
        self.assertGreaterEqual(summary["paper_case_study_count"], 4)
        self.assertIn("verifier_repair", mechanisms)
        self.assertIn("memory_bridge_prune", mechanisms)
        self.assertIn("promptedge_false_forward_block", mechanisms)
        self.assertIn("lifecycle_cost_control", mechanisms)
        self.assertTrue(summary["includes_required_mechanisms"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["next_required_run"], "R330_paper_tables_and_figures_plan")


if __name__ == "__main__":
    unittest.main()
