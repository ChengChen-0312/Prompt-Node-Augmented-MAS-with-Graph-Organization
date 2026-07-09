import unittest


class ForcedTemplateBadExactGateTests(unittest.TestCase):
    def test_bad_exact_gate_improves_r058_without_harm(self):
        from experiment.aqua.forced_template_bad_exact_gate import build_bad_exact_gate_summary

        summary = build_bad_exact_gate_summary()

        self.assertEqual(summary["rule"], "r088_bad_exact_contract_gate")
        self.assertEqual(summary["num_tasks"], 34)
        self.assertEqual(summary["baseline_solved"], 28)
        self.assertEqual(summary["dense_promptnode_solved"], 25)
        self.assertEqual(summary["gate_solved"], 29)
        self.assertEqual(summary["gate_fix_harm"], {"fix": 1, "harm": 0})
        self.assertEqual(summary["accepted_switch_tasks"], ["task_108"])
        self.assertEqual(summary["decision_field_violations"], 0)
        self.assertEqual(summary["claim_boundary"], "r058 replay gate candidate, not fresh accuracy")

    def test_bad_exact_gate_suppresses_conflict_and_split_exact_contracts(self):
        from experiment.aqua.forced_template_bad_exact_gate import decide_bad_exact_gate

        self.assertEqual(
            decide_bad_exact_gate(
                {
                    "router_option": "D",
                    "router_binding_status": "EXACT_MATCH",
                    "predicted_answer": "D",
                    "router_conflicts_with_direct_majority": True,
                    "direct_valid_vote_count": 2,
                    "direct_majority_count": 2,
                    "predicted_option_is_none_of_these": False,
                    "has_promptnode_graph": True,
                }
            )["reason"],
            "exact_conflicts_direct_majority",
        )
        self.assertEqual(
            decide_bad_exact_gate(
                {
                    "router_option": "C",
                    "router_binding_status": "EXACT_MATCH",
                    "predicted_answer": "C",
                    "router_conflicts_with_direct_majority": False,
                    "direct_valid_vote_count": 2,
                    "direct_majority_count": 1,
                    "predicted_option_is_none_of_these": False,
                    "has_promptnode_graph": True,
                }
            )["reason"],
            "exact_single_vote_split",
        )


if __name__ == "__main__":
    unittest.main()
