import unittest

import networkx as nx


class PromptNodeRoleTests(unittest.TestCase):
    def test_aqua_role_tables_include_prompt_node_roles(self):
        from experiment.aqua.aqua_prompt_set import ROLE_DESCRIPTION as experiment_roles
        from mas_framework.prompt.AQuA_prompt_set import ROLE_DESCRIPTION as runtime_roles

        expected_roles = {"PN_Memory", "PN_Verifier", "PN_Router"}

        self.assertTrue(expected_roles.issubset(experiment_roles))
        self.assertTrue(expected_roles.issubset(runtime_roles))
        for role in expected_roles:
            self.assertIn("Prompt Node", experiment_roles[role])
            self.assertEqual(experiment_roles[role], runtime_roles[role])

    def test_real_agent_role_filter_excludes_prompt_node_roles(self):
        from experiment.aqua.aqua_prompt_set import ROLE_DESCRIPTION
        from experiment.aqua.prompt_node_graph import get_real_agent_roles

        real_roles = get_real_agent_roles(ROLE_DESCRIPTION)

        self.assertEqual(
            real_roles,
            ("Math Solver", "Mathematical Analyst", "Programming Expert", "Inspector"),
        )
        self.assertTrue(all(not role.startswith("PN_") for role in real_roles))

    def test_augment_graph_with_prompt_nodes_appends_virtual_nodes_and_edges(self):
        from experiment.aqua.prompt_node_graph import (
            PN_ROLES,
            augment_graph_with_prompt_nodes,
            is_prompt_node_role,
        )

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver", label=0)
        graph.add_node(1, role="Inspector", label=1)
        graph.add_edge(0, 1, label=1)

        augmented = augment_graph_with_prompt_nodes(
            graph, policy="memory_verifier_router"
        )

        roles_by_node = {node: data["role"] for node, data in augmented.nodes(data=True)}
        prompt_nodes = [
            node for node, role in roles_by_node.items() if is_prompt_node_role(role)
        ]

        self.assertEqual(tuple(roles_by_node[node] for node in prompt_nodes), PN_ROLES)
        self.assertEqual(augmented.number_of_nodes(), 5)
        self.assertIn((0, prompt_nodes[0]), augmented.edges())
        self.assertIn((1, prompt_nodes[0]), augmented.edges())
        self.assertIn((prompt_nodes[0], prompt_nodes[1]), augmented.edges())
        self.assertIn((prompt_nodes[1], prompt_nodes[2]), augmented.edges())
        self.assertNotIn((prompt_nodes[2], 1), augmented.edges())

    def test_prompt_node_augmentation_preserves_dag_execution_order(self):
        from experiment.aqua.prompt_node_graph import augment_graph_with_prompt_nodes

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver", label=0)
        graph.add_node(1, role="Inspector", label=1)
        graph.add_edge(0, 1, label=1)

        augmented = augment_graph_with_prompt_nodes(
            graph, policy="memory_verifier_router"
        )

        self.assertTrue(nx.is_directed_acyclic_graph(augmented))

    def test_canonicalize_generated_prompt_nodes_replaces_invalid_pn_subgraph(self):
        from experiment.aqua.prompt_node_graph import canonicalize_prompt_node_topology

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver", label=0)
        graph.add_node(1, role="Programming Expert", label=1)
        graph.add_node(2, role="PN_Router", label=2)
        graph.add_node(3, role="PN_Router", label=3)
        graph.add_edge(0, 1, label=1)
        graph.add_edge(0, 3, label=1)
        graph.add_edge(1, 2, label=1)

        normalized = canonicalize_prompt_node_topology(
            graph, policy="canonicalize_generated"
        )

        roles = [normalized.nodes[n]["role"] for n in normalized.nodes()]
        self.assertEqual(roles.count("PN_Memory"), 1)
        self.assertEqual(roles.count("PN_Verifier"), 1)
        self.assertEqual(roles.count("PN_Router"), 1)
        self.assertEqual(roles[:2], ["Math Solver", "Programming Expert"])
        self.assertIn((0, 1), normalized.edges())
        self.assertIn((0, 2), normalized.edges())
        self.assertIn((1, 2), normalized.edges())
        self.assertIn((2, 3), normalized.edges())
        self.assertIn((3, 4), normalized.edges())
        self.assertTrue(nx.is_directed_acyclic_graph(normalized))

    def test_canonicalize_generated_leaves_no_pn_graph_unchanged(self):
        from experiment.aqua.prompt_node_graph import canonicalize_prompt_node_topology

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver", label=0)
        graph.add_node(1, role="Inspector", label=1)
        graph.add_edge(0, 1, label=1)

        normalized = canonicalize_prompt_node_topology(
            graph, policy="canonicalize_generated"
        )

        self.assertEqual(
            [normalized.nodes[n]["role"] for n in normalized.nodes()],
            ["Math Solver", "Inspector"],
        )
        self.assertEqual(list(normalized.edges()), [(0, 1)])


if __name__ == "__main__":
    unittest.main()
