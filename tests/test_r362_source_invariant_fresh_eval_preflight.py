import unittest


class TestR362SourceInvariantFreshEvalPreflight(unittest.TestCase):
    def test_preflight_builds_fresh_arg_and_promptnode_candidate_manifests_without_leakage(self):
        from experiment.mmlu.r362_source_invariant_fresh_eval_preflight import build_fresh_preflight

        records, summary = build_fresh_preflight()

        self.assertEqual(summary["run_id"], "R362")
        self.assertEqual(summary["tasks"], 48)
        self.assertEqual(summary["task_family_counts"], {"mmlu_nonstem": 24, "mmlu_stem": 24})
        self.assertEqual(summary["api_records"], 96)
        self.assertEqual(summary["planned_arg_baseline_calls"], 48)
        self.assertEqual(summary["planned_promptnode_candidate_calls"], 48)
        self.assertEqual(summary["overlap_with_excluded_task_count"], 0)
        self.assertTrue(summary["leakage_pass"])
        self.assertEqual(summary["policy_model"], "R360_source_invariant_graph_policy")
        self.assertEqual(summary["policy_threshold"], 0.7)
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(set(row["control_variant"] for row in records), {"arg_baseline_direct_api", "promptnode_candidate_api"})
        self.assertEqual(summary["next_required_run"], "R363_source_invariant_fresh_eval_api_execution")


if __name__ == "__main__":
    unittest.main()
