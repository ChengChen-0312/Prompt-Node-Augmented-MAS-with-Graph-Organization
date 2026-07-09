import unittest


class GoalAuditR126R130Tests(unittest.TestCase):
    def test_audit_corrects_rank_only_path_after_router_none_diagnosis(self):
        from experiment.aqua.goal_audit_r126_r130 import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["rule"], "r130_goal_audit_r126_r130")
        self.assertEqual(summary["status"], "aligned_after_correction")
        self.assertEqual(summary["goal_window"], ["R126", "R127", "R128", "R129", "R130"])
        self.assertTrue(summary["drift_detected"])
        self.assertEqual(
            summary["drift_type"],
            "rank_only_high_fanin_path_mistook_final_coercion_for_clean_fix",
        )
        self.assertFalse(summary["r126_uses_tail34_training_source"])
        self.assertFalse(summary["r127_uses_tail34_outputs_for_rank_selection"])
        self.assertEqual(summary["r127_switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["r128_selected_accuracy"], "3/4")
        self.assertEqual(summary["r128_clean_fix_harm"], "0/0")
        self.assertFalse(summary["r128_smoke_gate_passed"])
        self.assertEqual(summary["r129_router_none_no_exact_runs"], "3/3")
        self.assertTrue(summary["r129_historical_success_is_nearest_choice_coercion"])
        self.assertFalse(summary["r129_rank_selection_sufficient"])
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["next_protocol"],
            "deterministic_none_guard_or_exact_option_repair_before_api",
        )
        self.assertEqual(summary["next_goal_audit_due"], "R135")
        self.assertEqual(
            summary["claim_boundary"],
            "five-iteration goal audit and correction, not an accuracy result",
        )


if __name__ == "__main__":
    unittest.main()
