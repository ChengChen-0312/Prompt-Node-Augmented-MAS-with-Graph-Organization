import unittest

from experiment.mmlu.r186_promptedge_short_pretrain import (
    build_pretrain_args,
    infer_observed_role_mapping,
    split_graphs,
)


class TestR186MMLUPromptEdgeShortPretrain(unittest.TestCase):
    def test_split_graphs_keeps_train_and_validation_nonempty(self):
        graphs = list(range(10))
        train_graphs, val_graphs = split_graphs(graphs, seed=42)

        self.assertEqual(len(train_graphs) + len(val_graphs), len(graphs))
        self.assertGreater(len(train_graphs), 0)
        self.assertGreater(len(val_graphs), 0)

    def test_build_pretrain_args_is_no_api_cpu_graph_policy_config(self):
        args = build_pretrain_args(
            data_dir="data",
            output_dir="out",
            epochs=1,
            batch_size=8,
            lr=1e-4,
            seed=42,
        )

        self.assertEqual(args.dataset, "mmlu")
        self.assertEqual(args.data_dir, "data")
        self.assertEqual(args.experiment_path, "out")
        self.assertEqual(args.device, "cpu")
        self.assertTrue(args.pretrain)
        self.assertEqual(args.epochs, 1)
        self.assertEqual(args.batch_size, 8)

    def test_infer_observed_role_mapping_excludes_unused_promptnode_roles(self):
        import networkx as nx

        graph = nx.DiGraph()
        graph.add_node(0, role="Critic")
        graph.add_node(1, role="Mathematician")

        role_to_id, id_to_role = infer_observed_role_mapping(
            [graph],
            fallback_role_to_id={
                "Critic": 0,
                "Mathematician": 1,
                "PN_Memory": 2,
            },
        )

        self.assertEqual(set(role_to_id), {"Critic", "Mathematician"})
        self.assertEqual(id_to_role, {0: "Critic", 1: "Mathematician"})


if __name__ == "__main__":
    unittest.main()
