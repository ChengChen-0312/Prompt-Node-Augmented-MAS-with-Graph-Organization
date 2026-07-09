import unittest


class TestR309NegativeControls(unittest.TestCase):
    def test_negative_controls_block_training_but_do_not_beat_r306(self):
        from experiment.mmlu.r309_negative_controls import build_negative_control_summary, run_controls

        rows, summary = run_controls()
        control_names = set(summary["controls"])

        self.assertEqual(summary["run_id"], "R309")
        self.assertEqual(summary["reference"]["r306_main97"], "95/97")
        self.assertEqual(summary["controls"]["no_nonmath_promptnodes"]["main97"], "93/97")
        self.assertTrue(
            {
                "no_nonmath_promptnodes",
                "random_forward_same_budget",
                "always_forward_candidate_nodes",
                "no_safety_gate_unsafe_forward",
                "random_promptnode_type_same_budget",
                "no_lifecycle_prune_disabled",
            }.issubset(control_names)
        )
        self.assertFalse(summary["cheap_control_matches_or_beats_r306"])
        self.assertFalse(summary["training_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R310_transfer_preflight")
        self.assertGreater(len(rows), 0)

        rebuilt = build_negative_control_summary(rows)
        self.assertEqual(rebuilt["controls"]["random_forward_same_budget"]["main_records"], 97)

    def test_no_safety_gate_exposes_harm(self):
        from experiment.mmlu.r309_negative_controls import run_controls

        _, summary = run_controls()

        unsafe = summary["controls"]["no_safety_gate_unsafe_forward"]
        self.assertGreater(unsafe["main_harms"], 0)
        self.assertLess(unsafe["main_correct"], summary["reference"]["r306_main_correct"])


if __name__ == "__main__":
    unittest.main()
