import unittest


class TestR346ToolBackedPromptnodeLocalPreflight(unittest.TestCase):
    def test_local_preflight_repairs_r337_wrong_tasks_without_api_or_label_leakage(self):
        from experiment.mmlu.r346_tool_backed_promptnode_local_preflight import build_local_preflight

        records, summary = build_local_preflight()
        by_task = {row["task_id"]: row for row in records}

        self.assertEqual(summary["run_id"], "R346")
        self.assertEqual(summary["records"], 4)
        self.assertEqual(summary["api_calls"], 0)
        self.assertFalse(summary["uses_true_answers_in_tool"])
        self.assertFalse(summary["uses_task_ids_or_known_wrong_items"])
        self.assertEqual(summary["forwarded_candidate_count"], 4)
        self.assertEqual(summary["candidate_correct_count"], 4)
        self.assertEqual(summary["candidate_repairs_baseline_count"], 4)
        self.assertEqual(summary["candidate_harms_baseline_count"], 0)
        self.assertEqual(by_task["MMLU-high_school_mathematics_test-0"]["candidate_label"], "D")
        self.assertEqual(by_task["MMLU-college_mathematics_test-1"]["candidate_label"], "D")
        self.assertEqual(by_task["MMLU-college_mathematics_test-2"]["candidate_label"], "D")
        self.assertEqual(by_task["MMLU-college_chemistry_test-3"]["candidate_label"], "B")
        self.assertTrue(all(row["promptedge_contract_pass"] for row in records))
        self.assertEqual(summary["next_required_run"], "R347_tool_backed_promptnode_prospective_replay24")


if __name__ == "__main__":
    unittest.main()
