import unittest


class TestR399ContrastiveVerifierTargetedPreflight(unittest.TestCase):
    def test_preflight_builds_targeted_contrastive_probe(self):
        from experiment.mmlu.r399_contrastive_verifier_targeted_preflight import build_targeted_preflight

        records, summary = build_targeted_preflight()

        self.assertEqual(summary["run_id"], "R399")
        self.assertEqual(summary["targeted_tasks"], 7)
        self.assertEqual(summary["api_records"], 7)
        self.assertEqual(summary["planned_contrastive_candidate_calls"], 7)
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R400_contrastive_verifier_targeted_api_execution")
        self.assertEqual({row["control_variant"] for row in records}, {"contrastive_verifier_candidate_api"})


if __name__ == "__main__":
    unittest.main()
