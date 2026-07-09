import unittest


class TestR409NonmathCurriculumApiExecution(unittest.TestCase):
    def test_plan_and_parser_are_available_without_api_execution(self):
        from experiment.mmlu.r409_nonmath_curriculum_api_execution import (
            build_api_execution_plan,
            conservative_curriculum_gate,
            parse_curriculum_response,
        )

        plan = build_api_execution_plan()

        self.assertEqual(plan["run_id"], "R409")
        self.assertTrue(plan["leakage_pass"])
        self.assertFalse(plan["api_executed"])
        self.assertGreater(plan["tasks"], 0)
        self.assertEqual(plan["api_calls_planned"], plan["tasks"] * 2)
        self.assertEqual(plan["next_required_run"], "R409_execute_with_api_or_R410_analyze_if_executed")

        parsed = parse_curriculum_response(
            """```json
            {
              "candidate_label": "B",
              "confidence": 0.91,
              "node_agreement_count": 4,
              "node_disagreement_count": 0,
              "contradiction_count": 0,
              "ambiguity_flag": false,
              "definition_anchor_confidence": 0.88,
              "adversarial_challenge_pass": true,
              "nearest_distractor_margin": 0.31,
              "option_binding_contract_pass": true,
              "memory_bridge_write_confidence": 0.9,
              "rationale": "Option B satisfies the instruction."
            }
            ```"""
        )

        self.assertEqual(parsed["candidate_label"], "B")
        self.assertTrue(parsed["parse_ok"])
        self.assertTrue(conservative_curriculum_gate(parsed)["forward"])

        blocked = dict(parsed)
        blocked["contradiction_count"] = 1
        self.assertFalse(conservative_curriculum_gate(blocked)["forward"])


if __name__ == "__main__":
    unittest.main()
