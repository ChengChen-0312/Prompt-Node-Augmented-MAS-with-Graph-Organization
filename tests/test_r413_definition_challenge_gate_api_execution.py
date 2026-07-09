import unittest


class TestR413DefinitionChallengeGateApiExecution(unittest.TestCase):
    def test_plan_parser_and_gate_are_available_without_api_execution(self):
        from experiment.mmlu.r413_definition_challenge_gate_api_execution import (
            build_api_execution_plan,
            definition_challenge_gate,
            parse_definition_challenge_response,
        )

        plan = build_api_execution_plan()

        self.assertEqual(plan["run_id"], "R413")
        self.assertTrue(plan["leakage_pass"])
        self.assertFalse(plan["api_executed"])
        self.assertEqual(plan["api_calls_planned"], plan["tasks"] * 2)

        parsed = parse_definition_challenge_response(
            'preface {"candidate_label":"C","confidence":0.9,"node_agreement_count":4,'
            '"node_disagreement_count":0,"contradiction_count":0,"ambiguity_flag":false,'
            '"definition_anchor_confidence":0.9,"adversarial_challenge_pass":true,'
            '"nearest_distractor":"B","nearest_distractor_margin":0.16,'
            '"option_binding_contract_pass":true,"memory_bridge_write_confidence":0.85,'
            '"rationale":"ok"}'
        )

        self.assertEqual(parsed["candidate_label"], "C")
        self.assertTrue(parsed["parse_ok"])
        self.assertTrue(definition_challenge_gate(parsed)["forward"])

        blocked = dict(parsed)
        blocked["nearest_distractor_margin"] = 0.1
        self.assertFalse(definition_challenge_gate(blocked)["forward"])

        self.assertEqual(plan["next_required_run"], "R413_execute_with_api_or_R414_analyze_if_executed")


if __name__ == "__main__":
    unittest.main()
