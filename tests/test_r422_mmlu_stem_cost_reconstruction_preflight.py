import unittest


class TestR422MmluStemCostReconstructionPreflight(unittest.TestCase):
    def test_preflight_detects_missing_exact_cost_and_routes_to_probe(self):
        from experiment.mmlu.r422_mmlu_stem_cost_reconstruction_preflight import build_cost_reconstruction_preflight

        summary = build_cost_reconstruction_preflight()

        self.assertEqual(summary["run_id"], "R422")
        self.assertTrue(summary["source_results_found"])
        self.assertEqual(summary["source_records"], 100)
        self.assertFalse(summary["token_fields_found"])
        self.assertFalse(summary["exact_cost_reconstruction_possible"])
        self.assertTrue(summary["cost_probe_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R423_mmlu_stem_cost_probe_manifest")


if __name__ == "__main__":
    unittest.main()
