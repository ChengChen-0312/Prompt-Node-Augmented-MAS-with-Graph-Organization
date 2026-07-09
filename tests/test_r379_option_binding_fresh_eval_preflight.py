import unittest


class TestR379OptionBindingFreshEvalPreflight(unittest.TestCase):
    def test_preflight_builds_fresh_option_binding_manifest_without_r374_overlap(self):
        from experiment.mmlu.r379_option_binding_fresh_eval_preflight import build_option_binding_preflight

        records, summary = build_option_binding_preflight()

        self.assertEqual(summary["run_id"], "R379")
        self.assertEqual(summary["tasks"], 24)
        self.assertEqual(summary["api_records"], 48)
        self.assertEqual(summary["planned_arg_baseline_calls"], 24)
        self.assertEqual(summary["planned_option_binding_candidate_calls"], 24)
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["r374_overlap_free"])
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R380_option_binding_fresh_eval_api_execution")
        self.assertEqual({row["control_variant"] for row in records}, {"arg_baseline_direct_api", "history_option_binding_candidate_api"})


if __name__ == "__main__":
    unittest.main()
