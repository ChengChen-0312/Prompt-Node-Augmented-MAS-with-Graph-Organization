import unittest


class TestR374HistoryGuardedFreshEvalPreflight(unittest.TestCase):
    def test_preflight_builds_history_passage_fresh_manifest_without_leakage(self):
        from experiment.mmlu.r374_history_guarded_fresh_eval_preflight import build_history_preflight

        records, summary = build_history_preflight()

        self.assertEqual(summary["run_id"], "R374")
        self.assertEqual(summary["tasks"], 12)
        self.assertEqual(summary["api_records"], 24)
        self.assertEqual(summary["planned_arg_baseline_calls"], 12)
        self.assertEqual(summary["planned_history_candidate_calls"], 12)
        self.assertTrue(summary["leakage_pass"])
        self.assertEqual(summary["subject"], "high_school_us_history")
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(set(row["control_variant"] for row in records), {"arg_baseline_direct_api", "history_passage_candidate_api"})
        self.assertEqual(summary["next_required_run"], "R375_history_guarded_fresh_eval_api_execution")


if __name__ == "__main__":
    unittest.main()
