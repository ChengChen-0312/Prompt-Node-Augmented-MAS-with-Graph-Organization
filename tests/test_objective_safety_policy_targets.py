import unittest


class ObjectiveSafetyPolicyTargetsTests(unittest.TestCase):
    def test_exports_r095_policy_targets_without_outcome_or_audit_inputs(self):
        from experiment.aqua.objective_safety_policy_targets import (
            FORBIDDEN_POLICY_INPUT_FIELDS,
            build_policy_target_summary,
        )

        summary = build_policy_target_summary()

        self.assertEqual(summary["rule"], "r096_objective_safety_policy_targets")
        self.assertEqual(summary["num_rows"], 34)
        self.assertEqual(summary["target_action_counts"], {
            "fallback_to_arg": 32,
            "switch_to_objective": 2,
        })
        self.assertEqual(sorted(summary["switch_target_tasks"]), ["task_108", "task_250"])
        self.assertEqual(summary["clean_switch_target_tasks"], ["task_250"])
        self.assertEqual(summary["noisy_switch_target_tasks"], ["task_108"])
        self.assertEqual(summary["policy_input_field_violations"], 0)
        for row in summary["rows"]:
            self.assertFalse(FORBIDDEN_POLICY_INPUT_FIELDS.intersection(row["policy_input"]))
        self.assertEqual(
            summary["claim_boundary"],
            "policy-target export from R095 replay; no new accuracy result",
        )


if __name__ == "__main__":
    unittest.main()
