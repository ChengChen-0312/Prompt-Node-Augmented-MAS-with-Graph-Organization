import unittest

from mas_framework.agents.agent_registry import AgentRegistry
from mas_framework.agents import final_decision  # noqa: F401


class SelectivePromptNodeFinalTests(unittest.TestCase):
    def test_selective_prompt_node_final_is_registered(self):
        node = AgentRegistry.get(
            "SelectivePromptNodeFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        self.assertEqual(node.agent_name, "SelectivePromptNodeFinalRefer")

    def test_selective_prompt_includes_direct_and_router_evidence(self):
        node = AgentRegistry.get(
            "SelectivePromptNodeFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        raw_inputs = {
            "task": "Question? Choices: A)1 B)2 C)3 D)4 E)5",
        }
        spatial_info = {
            "solver": {
                "role": "Math Solver",
                "output": "Direct solver says option B because the value is 2.",
            },
            "router": {
                "role": "PN_Router",
                "output": (
                    "SUPPORTED_OPTION: C\n"
                    "BINDING_STATUS: CONFLICT\n"
                    "FINAL_EVIDENCE_SUMMARY: Router sees conflicting evidence."
                ),
            },
        }

        system_prompt, user_prompt = node._process_inputs(raw_inputs, spatial_info, {})

        self.assertIn("selective", system_prompt.lower())
        self.assertIn("PN_ACTION", user_prompt)
        self.assertIn("Agent-like Prompt Node", user_prompt)
        self.assertIn("Direct solver says option B", user_prompt)
        self.assertIn("SUPPORTED_OPTION: C", user_prompt)
        self.assertIn("BINDING_STATUS: CONFLICT", user_prompt)
        self.assertIn("MATH_TRUTH", user_prompt)
        self.assertIn("SUBMISSION_OPTION", user_prompt)
        self.assertIn("Never write `The answer is NONE`", user_prompt)

    def test_selective_prompt_falls_back_without_router_contract(self):
        node = AgentRegistry.get(
            "SelectivePromptNodeFinalRefer",
            domain="aqua",
            llm_name="mock",
        )
        raw_inputs = {
            "task": "Question? Choices: A)1 B)2 C)3 D)4 E)5",
        }
        spatial_info = {
            "solver": {
                "role": "Math Solver",
                "output": "Direct solver says option B because the value is 2.",
            },
        }

        system_prompt, user_prompt = node._process_inputs(raw_inputs, spatial_info, {})

        self.assertNotIn("PN_ACTION", user_prompt)
        self.assertIn("Direct solver says option B", user_prompt)


if __name__ == "__main__":
    unittest.main()
