import unittest


class TestR427ExternalIntegrityAuditRefresh(unittest.TestCase):
    def test_refresh_includes_new_nonmath_cost_and_lifecycle_artifacts(self):
        from experiment.mmlu.r427_external_integrity_audit_refresh import build_audit_refresh

        summary = build_audit_refresh()

        self.assertEqual(summary["run_id"], "R427")
        self.assertTrue(summary["external_review_required"])
        self.assertFalse(summary["external_review_executed"])
        self.assertFalse(summary["integrity_audit_complete"])
        critical = set(summary["critical_result_files"])
        self.assertIn("experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json", critical)
        self.assertIn("experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json", critical)
        self.assertIn("experiment/mmlu/run_logs/mmlu_r419_lifecycle_trace_events.jsonl", critical)
        self.assertIn("DefinitionChallenge", summary["review_prompt"])
        self.assertIn("probe_estimate_not_exact", summary["review_prompt"])
        self.assertEqual(summary["next_required_run"], "R428_updated_local_claim_integrity_precheck")


if __name__ == "__main__":
    unittest.main()
