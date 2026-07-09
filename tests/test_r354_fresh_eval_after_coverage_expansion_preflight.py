import unittest


class TestR354FreshEvalAfterCoverageExpansionPreflight(unittest.TestCase):
    def test_preflight_records_zero_coverage_on_new_fresh_split_and_blocks_api(self):
        from experiment.mmlu.r354_fresh_eval_after_coverage_expansion_preflight import build_fresh_preflight

        api_records, local_records, summary = build_fresh_preflight()

        self.assertEqual(summary["run_id"], "R354")
        self.assertEqual(summary["tasks"], 48)
        self.assertEqual(summary["task_family_counts"], {"mmlu_nonstem": 24, "mmlu_stem": 24})
        self.assertEqual(summary["api_manifest_records"], 48)
        self.assertEqual(summary["local_tool_records"], 48)
        self.assertEqual(summary["overlap_with_excluded_task_count"], 0)
        self.assertTrue(summary["leakage_pass"])
        self.assertEqual(summary["local_tool_forwarded_candidate_count"], 0)
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual({row["task_id"] for row in api_records}, {row["task_id"] for row in local_records})
        self.assertEqual(summary["next_required_run"], "R355_goal_audit_after_second_fresh_preflight")


if __name__ == "__main__":
    unittest.main()
