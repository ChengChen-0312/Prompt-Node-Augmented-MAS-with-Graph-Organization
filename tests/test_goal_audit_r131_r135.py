import unittest


class GoalAuditR131R135Tests(unittest.TestCase):
    def test_audit_confirms_edge_prompt_correction_without_broad_api_drift(self):
        from experiment.aqua.goal_audit_r131_r135 import build_goal_audit_summary

        summary = build_goal_audit_summary()

        self.assertEqual(summary["rule"], "r135_goal_audit_r131_r135")
        self.assertEqual(summary["status"], "aligned_continue_without_broad_api")
        self.assertEqual(summary["goal_window"], ["R131", "R132", "R133", "R134", "R135"])
        self.assertFalse(summary["drift_detected"])
        self.assertTrue(summary["maintained_update2_alignment"])
        self.assertTrue(summary["maintained_robustness_alignment"])
        self.assertTrue(summary["prompt_as_edge_correction_made"])
        self.assertTrue(summary["final_layer_no_longer_invents_repair"])
        self.assertTrue(summary["clean_gate_still_not_met"])
        self.assertFalse(summary["r132_smoke_gate_passed"])
        self.assertEqual(summary["r132_clean_fix_harm"], "0/0")
        self.assertFalse(summary["r134_r132_task250_has_repair_fields"])
        self.assertEqual(summary["r134_r132_task250_repair_gate_parser_prediction"], "None.")
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(summary["next_protocol"], "edge_prompt_repair_field_prompting_presmoke")
        self.assertEqual(summary["next_goal_audit_due"], "R140")
        self.assertEqual(
            summary["claim_boundary"],
            "five-iteration goal audit and correction, not an accuracy result",
        )


if __name__ == "__main__":
    unittest.main()
