import unittest


class TestR388MixedNonmathOptionBindingPreflight(unittest.TestCase):
    def test_preflight_builds_mixed_nonmath_manifest(self):
        from experiment.mmlu.r388_mixed_nonmath_option_binding_preflight import build_mixed_nonmath_preflight

        records, summary = build_mixed_nonmath_preflight()

        self.assertEqual(summary["run_id"], "R388")
        self.assertEqual(summary["tasks"], 24)
        self.assertEqual(summary["api_records"], 48)
        self.assertEqual(summary["subjects"], 6)
        self.assertEqual(summary["tasks_per_subject"], 4)
        self.assertEqual(summary["planned_arg_baseline_calls"], 24)
        self.assertEqual(summary["planned_semantic_option_binding_calls"], 24)
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R389_mixed_nonmath_option_binding_api_execution")
        self.assertEqual({row["control_variant"] for row in records}, {"arg_baseline_direct_api", "semantic_option_binding_candidate_api"})


if __name__ == "__main__":
    unittest.main()
