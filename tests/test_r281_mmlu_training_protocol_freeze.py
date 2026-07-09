import unittest


class TestR281MMLUTrainingProtocolFreeze(unittest.TestCase):
    def test_protocol_freezes_fair_arg_vs_promptnode_training_requirements(self):
        from experiment.mmlu.r281_training_protocol_freeze import build_r281_protocol_summary

        summary = build_r281_protocol_summary()

        self.assertEqual(summary["run_id"], "R281")
        self.assertTrue(summary["no_api"])
        self.assertTrue(summary["mps_available"])
        self.assertTrue(summary["arg_training_path"]["checkpoint_exists"])
        self.assertEqual(summary["arg_training_path"]["role_mapping_size"], 6)
        self.assertTrue(summary["promptnode_training_path"]["checkpoint_exists"])
        self.assertGreaterEqual(summary["promptnode_training_path"]["role_mapping_size"], 9)
        self.assertIn("PN_Memory", summary["promptnode_training_path"]["pn_roles_present"])
        self.assertIn("PN_Verifier", summary["promptnode_training_path"]["pn_roles_present"])
        self.assertIn("PN_Router", summary["promptnode_training_path"]["pn_roles_present"])
        self.assertTrue(summary["splits"]["full24_probe_exists"])
        self.assertTrue(summary["splits"]["transfer100_exists"])
        self.assertFalse(summary["claim_permissions"]["transfer_superiority_claim_allowed"])
        self.assertTrue(summary["training_authorized_next"])
        self.assertEqual(summary["next_runs"], ["R282_ARG_retrain", "R283_PromptNode_retrain"])


if __name__ == "__main__":
    unittest.main()
