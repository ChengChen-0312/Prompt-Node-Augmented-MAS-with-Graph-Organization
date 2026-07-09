import unittest


class TestR299GenericNoHarmVerifier(unittest.TestCase):
    def test_parse_verifier_response_accepts_switch_json(self):
        from experiment.mmlu.r299_generic_noharm_verifier import parse_verifier_response

        parsed = parse_verifier_response('{"action":"SWITCH","selected_label":"D","confidence":"high"}')

        self.assertEqual(parsed["action"], "SWITCH")
        self.assertEqual(parsed["selected_label"], "D")
        self.assertTrue(parsed["parse_ok"])

    def test_apply_verifier_response_keeps_arg_when_not_high_confidence_switch(self):
        from experiment.mmlu.r299_generic_noharm_verifier import apply_verifier_response

        row = {"arg_prediction": "B", "true_answer": "D"}
        out = apply_verifier_response(row, '{"action":"KEEP_ARG","selected_label":"D"}', api_error="")

        self.assertEqual(out["predicted_answer"], "B")
        self.assertFalse(out["is_correct"])

    def test_apply_verifier_response_switches_only_legal_label(self):
        from experiment.mmlu.r299_generic_noharm_verifier import apply_verifier_response

        row = {"arg_prediction": "B", "true_answer": "D"}
        out = apply_verifier_response(
            row,
            '{"action":"SWITCH","selected_label":"D","confidence":"high"}',
            api_error="",
        )

        self.assertEqual(out["predicted_answer"], "D")
        self.assertTrue(out["is_correct"])


if __name__ == "__main__":
    unittest.main()
