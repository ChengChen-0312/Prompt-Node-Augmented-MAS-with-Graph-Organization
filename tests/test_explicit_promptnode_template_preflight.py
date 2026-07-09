import unittest


class ExplicitPromptNodeTemplatePreflightTests(unittest.TestCase):
    def test_preflight_identifies_candidate_evidence_without_permitting_broad_api(self):
        from experiment.aqua.explicit_promptnode_template_preflight import (
            build_explicit_promptnode_template_preflight_summary,
        )

        summary = build_explicit_promptnode_template_preflight_summary()

        self.assertEqual(summary["rule"], "r123_explicit_promptnode_template_preflight")
        self.assertTrue(summary["preflight_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertEqual(summary["regression_tasks"], ["task_8", "task_108", "task_188", "task_250"])
        self.assertEqual(summary["candidate_source_tasks"], "4/4")
        self.assertEqual(summary["candidate_tasks_with_update2_metadata"], "4/4")
        self.assertEqual(summary["candidate_tasks_with_forbidden_field_violations"], "0/4")
        self.assertEqual(summary["top_candidate_promptnode_roles"], ["PN_Memory", "PN_Router", "PN_Verifier"])
        self.assertEqual(summary["r097_api_required_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["r097_fallback_tasks_in_regression_set"], ["task_8", "task_188"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "same_four_task_explicit_template_guarded_smoke",
        )
        self.assertEqual(
            summary["claim_boundary"],
            "preflight over explicit PromptNode template candidates; no API, accuracy, or cost result",
        )


if __name__ == "__main__":
    unittest.main()
