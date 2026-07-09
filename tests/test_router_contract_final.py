import unittest


class RouterContractFinalTests(unittest.TestCase):
    def test_extract_router_contracts_parses_machine_readable_fields(self):
        from mas_framework.agents.final_decision import extract_router_contracts

        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: A\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: Alan-only event is exactly option A.\n"
                ),
            },
            "solver": {"role": "Math Solver", "output": "The answer is C"},
        }

        contracts = extract_router_contracts(spatial_info)

        self.assertEqual(len(contracts), 1)
        self.assertEqual(contracts[0]["supported_option"], "A")
        self.assertEqual(contracts[0]["binding_status"], "EXACT_MATCH")
        self.assertIn("Alan-only", contracts[0]["final_evidence_summary"])

    def test_router_contract_final_is_registered(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "RouterContractFinalRefer",
            domain="aqua",
            llm_name="mock",
        )

        self.assertEqual(agent.agent_name, "RouterContractFinalRefer")

    def test_router_contract_final_prompt_is_not_aqua_specific(self):
        from mas_framework.agents.final_decision import RouterContractFinalRefer

        agent = RouterContractFinalRefer(domain="mmlu", llm_name="mock")
        system_prompt, _user_prompt = agent._process_inputs(
            {"task": "Q Choices: A)1 B)2 C)3 D)4"},
            {
                "router": {
                    "role": "PN_Router",
                    "output": (
                        "SUPPORTED_OPTION: A\n"
                        "BINDING_STATUS: EXACT_MATCH\n"
                        "FINAL_EVIDENCE_SUMMARY: Directly matches option A.\n"
                    ),
                }
            },
            {},
        )

        self.assertIn("multiple-choice task", system_prompt)
        self.assertNotIn("AQuA", system_prompt)

    def test_conservative_router_final_abstains_on_weak_binding(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "ConservativeRouterContractFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: E\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "FINAL_EVIDENCE_SUMMARY: The computed value is not in the choices.\n"
                ),
            },
            "solver": {"role": "MathSolver", "output": "Direct solution supports option D. The answer is D"},
        }

        system_prompt, user_prompt = agent._process_inputs(
            {"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"},
            spatial_info,
            {},
        )

        self.assertIn("weak option binding", system_prompt)
        self.assertIn("Direct solution supports option D", user_prompt)
        self.assertNotIn("SUPPORTED_OPTION: E", user_prompt)

    def test_conservative_router_final_uses_strong_binding(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "ConservativeRouterContractFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: A\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: Calculation directly matches option A.\n"
                ),
            },
            "solver": {"role": "MathSolver", "output": "The answer is C"},
        }

        _system_prompt, user_prompt = agent._process_inputs(
            {"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"},
            spatial_info,
            {},
        )

        self.assertIn("Terminal router contracts", user_prompt)
        self.assertIn("SUPPORTED_OPTION: A", user_prompt)
        self.assertIn("Calculation directly matches option A", user_prompt)

    def test_extract_direct_option_votes_ignores_prompt_nodes(self):
        from mas_framework.agents.final_decision import extract_direct_option_votes

        spatial_info = {
            "solver_a": {"role": "MathSolver", "output": "Reasoning... The answer is D"},
            "solver_b": {"role": "Inspector", "output": "I agree. The answer is D"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: A\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: Router supports A.\n"
                ),
            },
            "solver_bad": {"role": "MathSolver", "output": "No final option"},
        }

        self.assertEqual(extract_direct_option_votes(spatial_info), ["D", "D"])

    def test_summarize_pn_utility_features_marks_conflict(self):
        from mas_framework.agents.final_decision import summarize_pn_utility_features

        spatial_info = {
            "solver_a": {"role": "MathSolver", "output": "The answer is D"},
            "solver_b": {"role": "Inspector", "output": "The answer is D"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: A\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: Router supports A.\n"
                ),
            },
        }

        features = summarize_pn_utility_features(spatial_info)

        self.assertEqual(features["direct_majority_option"], "D")
        self.assertEqual(features["direct_majority_count"], 2)
        self.assertEqual(features["strong_router_options"], ["A"])
        self.assertTrue(features["strong_router_conflicts_with_direct_majority"])

    def test_calibrated_selector_prefers_direct_majority_over_weak_pn(self):
        from mas_framework.agents.final_decision import select_calibrated_pn_utility_answer

        spatial_info = {
            "solver_a": {"role": "MathSolver", "output": "The answer is D"},
            "solver_b": {"role": "Inspector", "output": "The answer is D"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "FINAL_EVIDENCE_SUMMARY: Computed value is absent from choices.\n"
                ),
            },
        }

        self.assertEqual(select_calibrated_pn_utility_answer(spatial_info), "D")

    def test_calibrated_selector_prefers_direct_majority_over_conflicting_strong_pn(self):
        from mas_framework.agents.final_decision import select_calibrated_pn_utility_answer

        spatial_info = {
            "solver_a": {"role": "MathSolver", "output": "The answer is B"},
            "solver_b": {"role": "MathSolver", "output": "The answer is B"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: C\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: Router supports C.\n"
                ),
            },
        }

        self.assertEqual(select_calibrated_pn_utility_answer(spatial_info), "B")

    def test_calibrated_selector_uses_strong_pn_without_direct_majority(self):
        from mas_framework.agents.final_decision import select_calibrated_pn_utility_answer

        spatial_info = {
            "solver_a": {"role": "MathSolver", "output": "No valid final answer"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: A\n"
                    "BINDING_STATUS: EQUIVALENT_FORM\n"
                    "FINAL_EVIDENCE_SUMMARY: Router supports A.\n"
                ),
            },
        }

        self.assertEqual(select_calibrated_pn_utility_answer(spatial_info), "A")

    def test_calibrated_selector_falls_back_when_uncertain(self):
        from mas_framework.agents.final_decision import select_calibrated_pn_utility_answer

        spatial_info = {
            "solver_a": {"role": "MathSolver", "output": "The answer is B"},
            "solver_b": {"role": "MathSolver", "output": "The answer is C"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: A\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: Router supports A.\n"
                ),
            },
        }

        self.assertIsNone(select_calibrated_pn_utility_answer(spatial_info))

    def test_calibrated_final_returns_deterministic_answer_when_selected(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "CalibratedPNUtilityFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "solver_a": {"role": "MathSolver", "output": "The answer is D"},
            "solver_b": {"role": "Inspector", "output": "The answer is D"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "FINAL_EVIDENCE_SUMMARY: Computed value is absent from choices.\n"
                ),
            },
        }

        self.assertEqual(
            agent._execute({"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"}, spatial_info, {}),
            "The answer is D",
        )

    def test_calibrated_final_falls_back_to_conservative_prompt_when_uncertain(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "CalibratedPNUtilityFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "solver_a": {"role": "MathSolver", "output": "The answer is B"},
            "solver_b": {"role": "MathSolver", "output": "The answer is C"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: A\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: Router supports A.\n"
                ),
            },
        }

        response = agent._execute({"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"}, spatial_info, {})

        self.assertIn("Terminal router contracts", response)
        self.assertIn("SUPPORTED_OPTION: A", response)

    def test_deterministic_router_final_uses_single_strong_contract(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "DeterministicRouterContractFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: B\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: Computed value exactly matches option B.\n"
                ),
            },
        }

        self.assertEqual(
            agent._execute({"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"}, spatial_info, {}),
            "The answer is B",
        )

    def test_deterministic_router_final_abstains_on_router_none_without_direct_majority(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry
        from datasets.aqua_dataset import aqua_get_predict

        agent = AgentRegistry.get(
            "DeterministicRouterContractFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "FINAL_EVIDENCE_SUMMARY: Computed value is absent from choices.\n"
                ),
            },
        }

        response = agent._execute(
            {"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"},
            spatial_info,
            {},
        )

        self.assertEqual(response, "no valid option is supported")
        self.assertEqual(aqua_get_predict(response), "None.")

    def test_deterministic_router_final_uses_direct_majority_on_weak_router(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "DeterministicRouterContractFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "solver_a": {"role": "MathSolver", "output": "The answer is D"},
            "solver_b": {"role": "Inspector", "output": "The answer is D"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "FINAL_EVIDENCE_SUMMARY: Computed value is absent from choices.\n"
                ),
            },
        }

        self.assertEqual(
            agent._execute({"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"}, spatial_info, {}),
            "The answer is D",
        )

    def test_edge_prompt_repair_parses_explicit_repair_fields(self):
        from mas_framework.agents.final_decision import extract_edge_prompt_repair_candidates

        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION/CONFLICT\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.93\n"
                    "REPAIR_DISTANCE_RATIO: 0.000046\n"
                    "FINAL_EVIDENCE_SUMMARY: exact value is absent, repair candidate is E.\n"
                ),
            },
        }

        repairs = extract_edge_prompt_repair_candidates(spatial_info)

        self.assertEqual(len(repairs), 1)
        self.assertEqual(repairs[0]["repair_option"], "E")
        self.assertEqual(repairs[0]["repair_binding_status"], "NUMERIC_NEAREST_WITH_TYPO_CHECK")
        self.assertAlmostEqual(repairs[0]["repair_confidence"], 0.93)

    def test_edge_prompt_repair_selector_accepts_only_valid_explicit_repair(self):
        from mas_framework.agents.final_decision import select_edge_prompt_repair_answer

        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.93\n"
                    "REPAIR_DISTANCE_RATIO: 0.000046\n"
                    "FINAL_EVIDENCE_SUMMARY: repair edge validates E.\n"
                ),
            },
        }

        self.assertEqual(select_edge_prompt_repair_answer(spatial_info), "E")

    def test_edge_prompt_repair_selector_rejects_missing_repair_fields(self):
        from mas_framework.agents.final_decision import select_edge_prompt_repair_answer

        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION/CONFLICT\n"
                    "FINAL_EVIDENCE_SUMMARY: no exact option exists.\n"
                ),
            },
        }

        self.assertIsNone(select_edge_prompt_repair_answer(spatial_info))

    def test_edge_prompt_repair_selector_rejects_low_confidence_or_large_distance(self):
        from mas_framework.agents.final_decision import select_edge_prompt_repair_answer

        low_confidence = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.50\n"
                    "REPAIR_DISTANCE_RATIO: 0.000046\n"
                ),
            },
        }
        large_distance = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.93\n"
                    "REPAIR_DISTANCE_RATIO: 0.2\n"
                ),
            },
        }

        self.assertIsNone(select_edge_prompt_repair_answer(low_confidence))
        self.assertIsNone(select_edge_prompt_repair_answer(large_distance))

    def test_edge_prompt_repair_selectors_preserve_zero_distance_ratio(self):
        from mas_framework.agents.final_decision import (
            select_calibrated_edge_prompt_repair_answer,
            select_edge_prompt_repair_answer,
        )

        high_confidence = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.93\n"
                    "REPAIR_DISTANCE_RATIO: 0.0\n"
                ),
            },
        }
        calibrated_confidence = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.50\n"
                    "REPAIR_DISTANCE_RATIO: 0.0\n"
                ),
            },
        }

        self.assertEqual(select_edge_prompt_repair_answer(high_confidence), "E")
        self.assertEqual(
            select_calibrated_edge_prompt_repair_answer(calibrated_confidence),
            "E",
        )

    def test_edge_prompt_repair_final_returns_repaired_option(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "EdgePromptRepairContractFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.93\n"
                    "REPAIR_DISTANCE_RATIO: 0.000046\n"
                ),
            },
        }

        self.assertEqual(
            agent._execute({"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"}, spatial_info, {}),
            "The answer is E",
        )

    def test_edge_prompt_repair_final_keeps_abstention_without_repair_contract(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "EdgePromptRepairContractFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "FINAL_EVIDENCE_SUMMARY: no exact option exists.\n"
                ),
            },
        }

        self.assertEqual(
            agent._execute({"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"}, spatial_info, {}),
            "no valid option is supported",
        )

    def test_calibrated_edge_prompt_repair_accepts_close_forwarded_repair(self):
        from mas_framework.agents.final_decision import (
            select_calibrated_edge_prompt_repair_answer,
        )

        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.50\n"
                    "REPAIR_DISTANCE_RATIO: 0.000046\n"
                ),
            },
        }

        self.assertEqual(select_calibrated_edge_prompt_repair_answer(spatial_info), "E")

    def test_calibrated_edge_prompt_repair_rejects_contradiction_or_large_distance(self):
        from mas_framework.agents.final_decision import (
            select_calibrated_edge_prompt_repair_answer,
        )

        contradiction = {
            "solver_a": {"role": "MathSolver", "output": "The answer is D"},
            "solver_b": {"role": "Inspector", "output": "The answer is D"},
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.50\n"
                    "REPAIR_DISTANCE_RATIO: 0.000046\n"
                ),
            },
        }
        large_distance = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.50\n"
                    "REPAIR_DISTANCE_RATIO: 0.03\n"
                ),
            },
        }

        self.assertIsNone(select_calibrated_edge_prompt_repair_answer(contradiction))
        self.assertIsNone(select_calibrated_edge_prompt_repair_answer(large_distance))

    def test_calibrated_edge_prompt_repair_final_is_registered(self):
        import mas_framework.agents
        from mas_framework.agents.agent_registry import AgentRegistry

        agent = AgentRegistry.get(
            "CalibratedEdgePromptRepairContractFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        spatial_info = {
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: NONE\n"
                    "BINDING_STATUS: NO_EXACT_OPTION\n"
                    "REPAIR_OPTION: E\n"
                    "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                    "REPAIR_CONFIDENCE: 0.50\n"
                    "REPAIR_DISTANCE_RATIO: 0.000046\n"
                ),
            },
        }

        self.assertEqual(
            agent._execute({"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"}, spatial_info, {}),
            "The answer is E",
        )


if __name__ == "__main__":
    unittest.main()
