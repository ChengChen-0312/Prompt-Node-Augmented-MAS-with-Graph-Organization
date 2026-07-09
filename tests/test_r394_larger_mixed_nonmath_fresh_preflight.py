import unittest


class TestR394LargerMixedNonmathFreshPreflight(unittest.TestCase):
    def test_preflight_builds_larger_mixed_nonmath_manifest(self):
        from experiment.mmlu.r394_larger_mixed_nonmath_fresh_preflight import build_larger_mixed_preflight

        records, summary = build_larger_mixed_preflight()

        self.assertEqual(summary["run_id"], "R394")
        self.assertEqual(summary["tasks"], 48)
        self.assertEqual(summary["api_records"], 96)
        self.assertEqual(summary["subjects"], 8)
        self.assertEqual(summary["tasks_per_subject"], 6)
        self.assertEqual(summary["planned_arg_baseline_calls"], 48)
        self.assertEqual(summary["planned_semantic_option_binding_calls"], 48)
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R395_larger_mixed_nonmath_fresh_api_execution")
        self.assertEqual({row["control_variant"] for row in records}, {"arg_baseline_direct_api", "semantic_option_binding_candidate_api"})


if __name__ == "__main__":
    unittest.main()
