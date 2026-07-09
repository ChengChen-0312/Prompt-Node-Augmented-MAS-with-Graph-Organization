import unittest

import torch
from torch_geometric.data import Data

from experiment.mmlu.evaluate_mmlu import load_role_constraints
from mas_framework.graph.graph import TestGraph
from mas_framework.prompt import mmlu_prompt_set as framework_mmlu_prompt_set


class TestR181MMLUPromptNodeRoles(unittest.TestCase):
    def test_mmlu_prompt_registries_expose_promptnode_roles(self):
        required_roles = {"PN_Memory", "PN_Verifier", "PN_Router"}

        self.assertTrue(required_roles.issubset(framework_mmlu_prompt_set.ROLE_DESCRIPTION))
        self.assertTrue(required_roles.issubset(load_role_constraints()))

    def test_mmlu_testgraph_constructs_promptnode_graph_without_api_call(self):
        pyg = Data()
        pyg.x = [
            {"role": "Knowlegable Expert"},
            {"role": "PN_Memory"},
            {"role": "PN_Verifier"},
            {"role": "PN_Router"},
        ]
        pyg.edge_index = torch.tensor(
            [[0, 1, 2], [1, 2, 3]],
            dtype=torch.long,
        )
        pyg.num_nodes = 4
        pyg.task = (
            "Which option is correct?\n"
            "Option A: Alpha\n"
            "Option B: Beta\n"
            "Option C: Gamma\n"
            "Option D: Delta"
        )

        graph = TestGraph(
            domain="mmlu",
            llm_name="gpt-4o-2024-08-06",
            decision_method="FinalRefer",
            pyg_data=pyg,
        )

        roles = [getattr(node, "role", "") for node in graph.nodes.values()]
        agent_names = [getattr(node, "agent_name", "") for node in graph.nodes.values()]

        self.assertEqual(roles, ["Knowlegable Expert", "PN_Memory", "PN_Verifier", "PN_Router"])
        self.assertEqual(agent_names.count("PromptNode"), 3)


if __name__ == "__main__":
    unittest.main()
