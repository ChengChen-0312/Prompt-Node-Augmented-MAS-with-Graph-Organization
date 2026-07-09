import unittest


class TestR333ProspectiveSelectorEvalDesign(unittest.TestCase):
    def test_design_freezes_leakage_budget_and_success_criteria_before_api(self):
        from experiment.mmlu.r333_prospective_selector_eval_design import build_prospective_eval_design

        summary = build_prospective_eval_design()

        self.assertEqual(summary["run_id"], "R333")
        self.assertEqual(summary["protocol"]["eval_name"], "prospective_mmlu_selector_heldout")
        self.assertTrue(summary["protocol"]["exclude_training_manifest_hashes"])
        self.assertIn("task_id", summary["leakage_forbidden_prompt_fields"])
        self.assertIn("true_answer", summary["leakage_forbidden_prompt_fields"])
        self.assertTrue(summary["preflight_authorized_next"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertIn("no_harm_on_nonstem", summary["success_criteria"])
        self.assertIn("cost_not_worse_than_plain_requery", summary["success_criteria"])
        self.assertEqual(summary["next_required_run"], "R334_prospective_selector_eval_preflight")


if __name__ == "__main__":
    unittest.main()
