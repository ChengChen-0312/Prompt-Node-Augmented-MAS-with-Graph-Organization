import unittest


class TestR340AnswerBearingCandidateGeneratorDesign(unittest.TestCase):
    def test_design_adds_general_answer_bearing_verifier_families_without_label_leakage(self):
        from experiment.mmlu.r340_answer_bearing_candidate_generator_design import build_generator_design

        summary = build_generator_design()
        family_ids = {family["id"] for family in summary["candidate_generator_families"]}

        self.assertEqual(summary["run_id"], "R340")
        self.assertIn("option_by_option_symbolic_verifier", family_ids)
        self.assertIn("coordinate_geometry_verifier", family_ids)
        self.assertIn("algebraic_structure_verifier", family_ids)
        self.assertIn("chemistry_balancer_verifier", family_ids)
        self.assertFalse(summary["uses_true_answers"])
        self.assertFalse(summary["uses_dataset_specific_task_rules"])
        self.assertTrue(summary["preflight_authorized_next"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R341_answer_bearing_candidate_generator_preflight")


if __name__ == "__main__":
    unittest.main()
