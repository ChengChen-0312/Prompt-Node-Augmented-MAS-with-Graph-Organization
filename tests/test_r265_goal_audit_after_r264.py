import unittest

from experiment.aqua.r265_goal_audit_after_r264 import build_goal_audit_summary


class TestR265GoalAuditAfterR264(unittest.TestCase):
    def test_negative_strong_teacher_keeps_goal_aligned_but_blocks_distillation(self):
        summary = build_goal_audit_summary(
            {
                "oracle_teacher_accuracy": "31/34",
                "non_oracle_teacher_accuracy": "31/34",
                "dataset_disagreement_flags": ["task_139", "task_228", "task_59"],
                "leakage_pass": True,
                "api_errors": 0,
            }
        )

        self.assertFalse(summary["drift"])
        self.assertFalse(summary["sci_q2_ready"])
        self.assertEqual(summary["status"], "aligned_redirect_to_label_noise_and_low_cost_selector")
        self.assertIn("do_not_distill_r264_as_higher_teacher", summary["blocked_claims"])


if __name__ == "__main__":
    unittest.main()
