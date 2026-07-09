import unittest
from types import SimpleNamespace

import torch
from torch_geometric.data import Data


class PromptNodeExecutionTests(unittest.TestCase):
    def test_prompt_node_formats_predecessor_evidence_without_solving(self):
        from mas_framework.agents.prompt_node import PromptNode

        prompt_node = PromptNode(role="PN_Memory", domain="aqua", llm_name="mock")
        predecessor = SimpleNamespace(
            id="agent_a",
            role="Math Solver",
            outputs=["Reasoning text. The answer is C"],
        )
        prompt_node.spatial_predecessors = [predecessor]

        outputs = prompt_node.execute({"task": "What is 1+1? Choices: A)1 B)2"})

        self.assertEqual(len(outputs), 1)
        output = outputs[0]
        self.assertIn("VIRTUAL PROMPT NODE", output)
        self.assertIn("PN_Memory", output)
        self.assertIn("agent_a", output)
        self.assertIn("Math Solver", output)
        self.assertNotIn("The answer is B", output)

    def test_verifier_prompt_contains_option_binding_contract(self):
        from mas_framework.agents.prompt_node import PromptNode

        prompt_node = PromptNode(role="PN_Verifier", domain="aqua", llm_name="mock")
        predecessor = SimpleNamespace(
            id="solver",
            role="Math Solver",
            outputs=["Computed 13/15, then says The answer is E"],
        )
        prompt_node.spatial_predecessors = [predecessor]

        outputs = prompt_node.execute(
            {"task": "Question? Choices: A)1/18 B)1/9 C)23/90 D)5/18 E)13/45"}
        )

        output = outputs[0]
        self.assertIn("TARGET_AUDIT", output)
        self.assertIn("OPTION_BINDING_AUDIT", output)
        self.assertIn("NO_NEAREST_OPTION_RESCUE", output)
        self.assertIn("E) 13/45", output)

    def test_verifier_prompt_contains_repair_candidate_audit_contract(self):
        from mas_framework.agents.prompt_node import PromptNode

        prompt_node = PromptNode(role="PN_Verifier", domain="aqua", llm_name="mock")
        predecessor = SimpleNamespace(
            id="solver",
            role="Math Solver",
            outputs=["Computed value 1096010; options include E)1096061"],
        )
        prompt_node.spatial_predecessors = [predecessor]

        outputs = prompt_node.execute(
            {
                "task": (
                    "How many children? Choices: A)1095961 B)1065961 "
                    "C)1085961 D)1097961 E)1096061"
                )
            }
        )

        output = outputs[0]
        self.assertIn("REPAIR_CANDIDATE_AUDIT", output)
        self.assertIn("repair_option", output)
        self.assertIn("repair_distance_ratio", output)
        self.assertIn("repair_confidence", output)
        self.assertIn("do not convert repair into final A-E support", output)
        self.assertIn("NUMERIC_NEAREST_WITH_TYPO_CHECK", output)
        self.assertIn("never use EXACT_MATCH or EQUIVALENT_FORM as repair_binding_status", output)

    def test_router_prompt_contains_machine_readable_contract(self):
        from mas_framework.agents.prompt_node import PromptNode

        prompt_node = PromptNode(role="PN_Router", domain="aqua", llm_name="mock")
        predecessor = SimpleNamespace(
            id="verifier",
            role="PN_Verifier",
            outputs=[
                "OPTION_BINDING_AUDIT: candidate A exact; VERDICT: trust A"
            ],
        )
        prompt_node.spatial_predecessors = [predecessor]

        outputs = prompt_node.execute(
            {"task": "Question? Choices: A)1/18 B)1/9 C)23/90 D)5/18 E)13/45"}
        )

        output = outputs[0]
        self.assertIn("SUPPORTED_OPTION", output)
        self.assertIn("BINDING_STATUS", output)
        self.assertIn("FINAL_EVIDENCE_SUMMARY", output)
        self.assertIn("SUPPRESS_UNSUPPORTED_LABELS", output)
        self.assertIn("REPAIR_OPTION", output)
        self.assertIn("REPAIR_BINDING_STATUS", output)
        self.assertIn("REPAIR_CONFIDENCE", output)
        self.assertIn("REPAIR_DISTANCE_RATIO", output)
        self.assertIn("REPAIR_FORWARDING_REQUIRED", output)
        self.assertIn("SUPPORTED_OPTION: NONE may coexist with REPAIR_OPTION", output)
        self.assertIn("do not reset repair fields to NONE", output)

    def test_router_prompt_demotes_partial_overlap_and_truncated_verifier_evidence(self):
        from mas_framework.agents.prompt_node import PromptNode

        prompt_node = PromptNode(role="PN_Router", domain="aqua", llm_name="mock")
        predecessor = SimpleNamespace(
            id="verifier",
            role="PN_Verifier",
            outputs=[
                "OPTION_BINDING_AUDIT: option C partially overlaps but exceeds its upper bound. "
                "VERDICT: evidence truncated before final conflict resolution"
            ],
        )
        prompt_node.spatial_predecessors = [predecessor]

        outputs = prompt_node.execute(
            {"task": "Question? Choices: A)20<x<54 B)23<x<58 C)25<x<64 D)28<x<60 E)None"}
        )

        output = outputs[0]
        self.assertIn("PARTIAL_OVERLAP_IS_NOT_EXACT", output)
        self.assertIn("TRUNCATED_VERIFIER_IS_WEAK", output)
        self.assertIn("SUPPORTED_OPTION: NONE", output)
        self.assertIn("BINDING_STATUS: NO_EXACT_OPTION/CONFLICT", output)

    def test_testgraph_dispatches_prompt_node_roles_to_prompt_node_executor(self):
        import mas_framework.agents
        from mas_framework.agents.prompt_node import PromptNode
        from mas_framework.agents.math_solver import MathSolver
        from mas_framework.graph.graph import TestGraph

        pyg_data = Data()
        pyg_data.x = [
            {"role": "Math Solver", "constraint": ""},
            {"role": "PN_Memory", "constraint": ""},
        ]
        pyg_data.edge_index = torch.tensor([[0], [1]], dtype=torch.long)
        pyg_data.num_nodes = 2

        graph = TestGraph(
            domain="aqua",
            llm_name="gpt-4o-2024-08-06",
            decision_method="FinalRefer",
            pyg_data=pyg_data,
        )

        nodes = list(graph.nodes.values())
        self.assertIsInstance(nodes[0], MathSolver)
        self.assertIsInstance(nodes[1], PromptNode)
        self.assertEqual(nodes[1].role, "PN_Memory")

    def test_terminal_decision_exposure_connects_only_prompt_router(self):
        from mas_framework.graph.graph import TestGraph

        pyg_data = Data()
        pyg_data.x = [
            {"role": "Math Solver", "constraint": ""},
            {"role": "Programming Expert", "constraint": ""},
            {"role": "PN_Memory", "constraint": ""},
            {"role": "PN_Verifier", "constraint": ""},
            {"role": "PN_Router", "constraint": ""},
        ]
        pyg_data.edge_index = torch.tensor(
            [[0, 1, 2, 3], [2, 2, 3, 4]], dtype=torch.long
        )
        pyg_data.num_nodes = 5
        pyg_data.decision_exposure_policy = "terminal"

        graph = TestGraph(
            domain="aqua",
            llm_name="gpt-4o-2024-08-06",
            decision_method="FinalRefer",
            pyg_data=pyg_data,
        )
        graph.connect_decision_node()

        predecessor_roles = [
            node.role for node in graph.decision_node.spatial_predecessors
        ]
        self.assertEqual(predecessor_roles, ["PN_Router"])


if __name__ == "__main__":
    unittest.main()
