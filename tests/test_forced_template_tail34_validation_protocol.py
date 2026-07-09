import unittest


class ForcedTemplateTail34ValidationProtocolTests(unittest.TestCase):
    def test_protocol_freezes_same_model_full_tail34_gate_without_outcome_fields(self):
        from experiment.aqua.forced_template_tail34_validation_protocol import (
            build_validation_protocol,
        )

        protocol = build_validation_protocol()

        self.assertEqual(protocol["rule"], "r092_forced_template_tail34_validation_protocol")
        self.assertEqual(protocol["status"], "pre_registered_before_full_run")
        self.assertEqual(protocol["num_tasks"], 34)
        self.assertEqual(protocol["llm_name"], "gpt-4o-2024-08-06")
        self.assertEqual(protocol["forced_template_rank"], 1)
        self.assertEqual(protocol["gate_rule"], "r088_bad_exact_contract_gate")
        self.assertEqual(protocol["baseline_accuracy_reference"], "28/34")
        self.assertEqual(protocol["success_gate"]["minimum_gate_solved"], ">=29/34")
        self.assertEqual(protocol["success_gate"]["maximum_harm"], 0)
        self.assertEqual(
            protocol["claim_boundary"],
            "pre-registered full tail34 forced-template validation protocol, not a result",
        )
        self.assertFalse(
            set(protocol["decision_feature_fields"]).intersection(
                set(protocol["forbidden_outcome_fields"])
            )
        )


if __name__ == "__main__":
    unittest.main()
