import unittest


class SciQ2EvidenceGapPlanTests(unittest.TestCase):
    def test_plan_turns_r150_blockers_into_must_run_gates(self):
        from experiment.aqua.sci_q2_evidence_gap_plan import build_evidence_gap_plan_summary

        summary = build_evidence_gap_plan_summary()

        self.assertEqual(summary["rule"], "r151_sci_q2_evidence_gap_plan_before_more_api")
        self.assertTrue(summary["plan_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["blocking_gap_count"], 5)
        self.assertIn("transfer_checkpoint_resolution", summary["must_run_blocks"])
        self.assertIn("same_method_aqua_replicate", summary["must_run_blocks"])
        self.assertIn("cost_normalized_variant_or_accounting", summary["must_run_blocks"])
        self.assertTrue(summary["transfer_required_for_sci_q2"])
        self.assertTrue(summary["same_method_significance_required"])
        self.assertTrue(summary["cost_boundary_required"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "r152_mmlu_checkpoint_resolution_or_aqua_same_method_replicate_preflight",
        )


if __name__ == "__main__":
    unittest.main()
