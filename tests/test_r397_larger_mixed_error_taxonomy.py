import unittest


class TestR397LargerMixedErrorTaxonomy(unittest.TestCase):
    def test_error_taxonomy_identifies_next_method_work(self):
        from experiment.mmlu.r397_larger_mixed_error_taxonomy import build_error_taxonomy

        summary = build_error_taxonomy()

        self.assertEqual(summary["run_id"], "R397")
        self.assertEqual(summary["wrong_forward_count"], 3)
        self.assertEqual(summary["missed_fix_count"], 4)
        self.assertEqual(summary["candidate_correct_but_blocked_count"], 1)
        self.assertIn("wrong_forward_definition_misbinding", summary["root_causes"])
        self.assertIn("candidate_quality_failure", summary["root_causes"])
        self.assertIn("gate_over_pruning_for_candidate_type_option", summary["root_causes"])
        self.assertIn("abstention_or_schema_failure", summary["root_causes"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R398_nonmath_contrastive_verifier_design")


if __name__ == "__main__":
    unittest.main()
