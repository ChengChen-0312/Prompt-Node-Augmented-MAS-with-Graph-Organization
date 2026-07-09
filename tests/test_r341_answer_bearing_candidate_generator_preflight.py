import unittest


class TestR341AnswerBearingCandidateGeneratorPreflight(unittest.TestCase):
    def test_preflight_targets_wrong_tasks_with_general_verifier_prompts_without_label_leakage(self):
        from experiment.mmlu.r341_answer_bearing_candidate_generator_preflight import build_generator_preflight

        records, summary = build_generator_preflight()
        families = {row["verifier_family"] for row in records}

        self.assertEqual(summary["run_id"], "R341")
        self.assertEqual(summary["records"], 4)
        self.assertIn("coordinate_geometry_verifier", families)
        self.assertIn("algebraic_structure_verifier", families)
        self.assertIn("chemistry_balancer_verifier", families)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["uses_true_answers_in_prompt"])
        self.assertTrue(summary["api_probe_authorized_next"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertEqual(summary["next_required_run"], "R342_answer_bearing_candidate_generator_api_probe")


if __name__ == "__main__":
    unittest.main()
