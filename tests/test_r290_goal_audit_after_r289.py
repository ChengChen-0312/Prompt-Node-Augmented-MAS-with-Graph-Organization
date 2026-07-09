import unittest


class TestR290GoalAuditAfterR289(unittest.TestCase):
    def test_goal_audit_marks_negative_transfer_result_without_drift(self):
        from experiment.mmlu.r290_goal_audit_after_r289 import build_goal_audit

        r287 = {"selected_contract_ready_rate": 0.83}
        r289_rows = [
            {"task_id": "a", "is_correct": True},
            {"task_id": "b", "is_correct": False},
        ]
        baseline_rows = [
            {"task_id": "a", "is_correct": True},
            {"task_id": "b", "is_correct": True},
        ]

        summary = build_goal_audit(r287=r287, r289_rows=r289_rows, baseline_rows=baseline_rows)

        self.assertEqual(summary["run_id"], "R290")
        self.assertEqual(summary["goal_alignment"], "aligned_negative_transfer_result")
        self.assertFalse(summary["transfer_superiority_claim_supported"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["r289_correct"], 1)
        self.assertEqual(summary["baseline_correct_on_matched_tasks"], 2)
        self.assertEqual(summary["harms_vs_baseline"], 1)
        self.assertIn("R291_all_exposure_replay", summary["next_runs"])


if __name__ == "__main__":
    unittest.main()
