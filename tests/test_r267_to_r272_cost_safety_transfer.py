import unittest


class R267ToR272CostSafetyTransferTests(unittest.TestCase):
    def test_r267_combines_r068_cost_with_r095_safety(self):
        from experiment.aqua.r267_cost_safety_combined_selector import build_r267_summary

        summary = build_r267_summary()

        self.assertEqual(summary["run_id"], "R267")
        self.assertEqual(summary["official"]["accuracy"], "30/34")
        self.assertEqual(summary["exclude_59_139_228_correct_114"]["accuracy"], "31/31")
        self.assertEqual(summary["accepted_switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["suppressed_switch_tasks"], ["task_114", "task_59"])
        self.assertEqual(summary["cost_estimate"]["estimated_cost"], 3.597409)
        self.assertEqual(summary["claim_boundary"], "no_api_replay_over_r068_trigger_and_r095_safety_gate")

    def test_r268_student_policy_export_has_no_forbidden_feature_fields(self):
        from experiment.aqua.r268_low_cost_student_policy_export import build_r268_policy_export

        payload = build_r268_policy_export()

        self.assertEqual(payload["run_id"], "R268")
        self.assertEqual(payload["rows"], 34)
        self.assertEqual(payload["decision_field_violations"], 0)
        self.assertEqual(payload["accept_objective_tasks"], ["task_108", "task_250"])
        self.assertIn("PN_Verifier", payload["promptnode_roles"])
        self.assertIn("forward", payload["edge_actions"])
        self.assertTrue(payload["requires_training_before_accuracy_claim"])

    def test_r269_critical_smoke_replay_keeps_task114_audit_correct(self):
        from experiment.aqua.r269_critical_smoke_replay import build_r269_summary

        summary = build_r269_summary()

        self.assertEqual(summary["run_id"], "R269")
        self.assertEqual(summary["claim_boundary"], "no_api_critical_case_replay")
        self.assertIn("task_114", summary["critical_tasks"])
        self.assertEqual(summary["task_outcomes"]["task_114"]["r267_prediction"], "C")
        self.assertTrue(summary["task_outcomes"]["task_114"]["correct_if_task114_label_corrected_to_c"])
        self.assertEqual(summary["critical_official"]["fix_harm"], "2/0")

    def test_r270_goal_audit_keeps_course_to_transfer_boundary(self):
        from experiment.aqua.r270_goal_audit_cost_safety_transfer import build_r270_goal_audit

        summary = build_r270_goal_audit()

        self.assertEqual(summary["run_id"], "R270")
        self.assertTrue(summary["aligned_with_goal"])
        self.assertFalse(summary["drift_detected"])
        self.assertEqual(summary["next_required_stop"], "R272_transfer_boundary")

    def test_r271_tail34_final_table_reports_official_and_audit_clean(self):
        from experiment.aqua.r271_tail34_final_claim_table import build_r271_summary

        summary = build_r271_summary()

        self.assertEqual(summary["run_id"], "R271")
        self.assertEqual(summary["variants"]["R065"]["official"], "31/34")
        self.assertEqual(summary["variants"]["R267"]["official"], "30/34")
        self.assertEqual(summary["variants"]["R267"]["correct_task114"], "31/31")
        self.assertEqual(summary["recommended_main_text_claim"], "official_plus_audit_clean_scope_limited")

    def test_r272_transfer_boundary_narrows_claim_after_mmlu(self):
        from experiment.mmlu.r272_transfer_claim_boundary import build_r272_transfer_boundary

        summary = build_r272_transfer_boundary()

        self.assertEqual(summary["run_id"], "R272")
        self.assertEqual(summary["dataset"], "MMLU STEM tiny16 transfer diagnostic")
        self.assertFalse(summary["transfer_superiority_supported"])
        self.assertTrue(summary["non_aqua_transfer_completed"])
        self.assertEqual(summary["claim_revision"], "narrow_to_aqua_with_mmlu_negative_transfer_boundary")
        self.assertTrue(summary["stop_after_this_run"])


if __name__ == "__main__":
    unittest.main()
