import unittest


class Rank5GuardDeployabilityAuditTests(unittest.TestCase):
    def test_single_rank5_features_do_not_separate_task8_harm_from_task250_recovery(self):
        from experiment.aqua.rank5_guard_deployability_audit import build_deployability_summary

        summary = build_deployability_summary()

        self.assertEqual(summary["rule"], "r108_rank5_guard_deployability_audit")
        self.assertEqual(summary["num_tasks"], 4)
        self.assertEqual(summary["ambiguous_single_template_groups"], 1)
        self.assertEqual(summary["ambiguous_no_exact_diff_tasks"], ["task_8", "task_250"])
        self.assertEqual(summary["objective_features_separate_ambiguous_tasks"], True)
        self.assertEqual(summary["single_template_guard_sufficient"], False)
        self.assertEqual(summary["selector_input_field_violations"], 0)
        self.assertEqual(
            summary["claim_boundary"],
            "feature audit only; no accuracy or new selector claim",
        )


if __name__ == "__main__":
    unittest.main()
