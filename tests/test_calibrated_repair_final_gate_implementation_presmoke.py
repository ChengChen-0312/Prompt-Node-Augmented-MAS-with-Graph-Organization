import unittest


class CalibratedRepairFinalGateImplementationPresmokeTests(unittest.TestCase):
    def test_presmoke_registers_method_and_freezes_bounded_api_command(self):
        from experiment.aqua.calibrated_repair_final_gate_implementation_presmoke import (
            build_calibrated_repair_final_gate_implementation_presmoke,
            build_evaluate_command,
        )

        summary = build_calibrated_repair_final_gate_implementation_presmoke()
        command = build_evaluate_command()

        self.assertEqual(
            summary["rule"],
            "r144_calibrated_repair_final_gate_implementation_presmoke",
        )
        self.assertTrue(summary["presmoke_only"])
        self.assertTrue(summary["no_api_run"])
        self.assertTrue(summary["decision_method_registered"])
        self.assertTrue(summary["close_forwarded_repair_accepted"])
        self.assertTrue(summary["direct_contradiction_rejected"])
        self.assertTrue(summary["large_distance_rejected"])
        self.assertTrue(summary["r143_offline_gate_passed"])
        self.assertEqual(
            summary["decision_method"],
            "CalibratedEdgePromptRepairContractFinalRefer",
        )
        self.assertIn(
            "--decision_method CalibratedEdgePromptRepairContractFinalRefer",
            command,
        )
        self.assertTrue(summary["same_two_switch_task_smoke_allowed_next"])
        self.assertFalse(summary["broad_api_allowed_next"])


if __name__ == "__main__":
    unittest.main()
