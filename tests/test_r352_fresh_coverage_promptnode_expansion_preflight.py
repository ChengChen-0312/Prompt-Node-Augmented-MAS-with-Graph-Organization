import unittest


class TestR352FreshCoveragePromptnodeExpansionPreflight(unittest.TestCase):
    def test_expanded_promptnodes_gain_nonzero_dev_coverage_with_machine_evidence(self):
        from experiment.mmlu.r352_fresh_coverage_promptnode_expansion_preflight import build_expansion_preflight

        records, summary = build_expansion_preflight()
        by_task = {row["task_id"]: row for row in records}

        self.assertEqual(summary["run_id"], "R352")
        self.assertEqual(summary["records"], 48)
        self.assertTrue(summary["dev_set_only"])
        self.assertGreaterEqual(summary["forwarded_candidate_count"], 8)
        self.assertEqual(summary["candidate_correct_count"], summary["forwarded_candidate_count"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(by_task["MMLU-high_school_mathematics_test-5"]["candidate_label"], "B")
        self.assertEqual(by_task["MMLU-high_school_mathematics_test-6"]["candidate_label"], "C")
        self.assertEqual(by_task["MMLU-high_school_mathematics_test-7"]["candidate_label"], "A")
        self.assertEqual(by_task["MMLU-college_mathematics_test-4"]["candidate_label"], "C")
        self.assertEqual(by_task["MMLU-high_school_physics_test-7"]["candidate_label"], "C")
        self.assertEqual(by_task["MMLU-high_school_physics_test-8"]["candidate_label"], "A")
        self.assertEqual(by_task["MMLU-high_school_chemistry_test-4"]["candidate_label"], "B")
        self.assertEqual(by_task["MMLU-high_school_chemistry_test-5"]["candidate_label"], "C")
        self.assertEqual(summary["next_required_run"], "R353_fresh_eval_after_coverage_expansion_design")


if __name__ == "__main__":
    unittest.main()
