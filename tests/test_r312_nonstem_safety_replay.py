import unittest


class TestR312NonstemSafetyReplay(unittest.TestCase):
    def test_warning_only_candidate_cannot_override_arg(self):
        from experiment.mmlu.r312_nonstem_safety_replay_claim import apply_warning_only_safety_gate

        row = {
            "control_variant": "proposed_nonstem_promptnode_promptedge",
            "task_id": "t1",
            "arg_prediction": "A",
            "predicted_answer": "B",
            "true_answer": "A",
            "is_correct": False,
            "arg_is_correct": True,
            "parsed_guarded_response": {"action": "SWITCH", "final_label": "B", "confidence": "high"},
        }
        split = {"candidate": {"candidate_type": "instruction_ambiguity_verifier", "candidate_label": ""}}

        replayed = apply_warning_only_safety_gate(row, split)

        self.assertEqual(replayed["predicted_answer"], "A")
        self.assertTrue(replayed["is_correct"])
        self.assertFalse(replayed["harm"])
        self.assertEqual(replayed["safety_replay_reason"], "warning_only_candidate_no_answer_override")

    def test_r312_replay_recovers_no_harm_claim(self):
        from experiment.mmlu.r312_nonstem_safety_replay_claim import build_safety_replay_summary

        rows, summary = build_safety_replay_summary()

        self.assertEqual(summary["run_id"], "R312")
        self.assertEqual(summary["arg_main"], "37/40")
        self.assertEqual(summary["proposed_safety_replay_main"], "37/40")
        self.assertEqual(summary["fix_harm_vs_arg"], "0/0")
        self.assertTrue(summary["no_harm"])
        self.assertFalse(summary["beats_arg"])
        self.assertFalse(summary["training_authorized_next"])
        self.assertGreater(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
