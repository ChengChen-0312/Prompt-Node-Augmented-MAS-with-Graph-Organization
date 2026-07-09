import unittest


class TestR307ControlsTransferProtocol(unittest.TestCase):
    def test_protocol_requires_controls_and_transfer_before_training(self):
        from experiment.mmlu.r307_controls_transfer_protocol import build_protocol_summary

        summary = build_protocol_summary()

        self.assertEqual(summary["run_id"], "R307")
        self.assertFalse(summary["training_authorized_next"])
        self.assertIn("random_forward", summary["negative_controls"])
        self.assertIn("AQuA_tail34_audit_clean", summary["required_transfer_splits"])
        self.assertIn("MMLU_non_STEM_multiple_choice", summary["required_transfer_splits"])
        self.assertEqual(summary["current_best_main97"], "95/97")


if __name__ == "__main__":
    unittest.main()
