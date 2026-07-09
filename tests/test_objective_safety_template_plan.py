import unittest


class ObjectiveSafetyTemplatePlanTests(unittest.TestCase):
    def test_materializes_r096_switch_targets_as_explicit_promptnode_templates(self):
        from experiment.aqua.objective_safety_template_plan import (
            FORBIDDEN_SELECTOR_INPUT_FIELDS,
            build_template_plan_summary,
        )

        summary = build_template_plan_summary()

        self.assertEqual(summary["rule"], "r097_objective_safety_template_plan")
        self.assertEqual(summary["num_rows"], 34)
        self.assertEqual(
            summary["target_action_counts"],
            {"fallback_to_arg": 32, "switch_to_objective": 2},
        )
        self.assertEqual(sorted(summary["switch_target_tasks"]), ["task_108", "task_250"])
        self.assertEqual(summary["switch_tasks_with_template_candidates"], ["task_108", "task_250"])
        self.assertEqual(summary["missing_switch_template_tasks"], [])
        self.assertEqual(summary["selected_template_ranks"], {"task_108": 1, "task_250": 1})
        self.assertEqual(summary["clean_switch_target_tasks"], ["task_250"])
        self.assertEqual(summary["noisy_switch_target_tasks"], ["task_108"])
        self.assertEqual(summary["switch_targets_with_update2_metadata"], 2)
        self.assertEqual(summary["selector_input_field_violations"], 0)
        for row in summary["rows"]:
            self.assertFalse(
                FORBIDDEN_SELECTOR_INPUT_FIELDS.intersection(row["selector_input"])
            )
        self.assertEqual(
            summary["claim_boundary"],
            "explicit template plan from R096/R083; no new API or accuracy result",
        )


if __name__ == "__main__":
    unittest.main()
