import unittest

import torch


class ARGDesignerSamplingTests(unittest.TestCase):
    def test_sample_accepts_batched_task_embeddings(self):
        from experiment.aqua.aqua_adapter import AquaGraphDataset
        from experiment.utils import load_model

        model = load_model(
            "experiment/aqua/output/aqua_pn_graph_policy_r054_smoke",
            ef=True,
        )
        dataset = AquaGraphDataset(
            data_dir="experiment/ColdStartData_Aqua",
            data_dir_ef="experiment/FinetuneData_AQuA_PN_GraphPolicy_R053",
            sample_size=1,
            pretrain=False,
        )
        embedding = dataset.graph_list[0].graph["task_embedding"]
        if not isinstance(embedding, torch.Tensor):
            embedding = torch.tensor(embedding).float()
        task_embeddings = embedding.to(model.args.device).unsqueeze(0).repeat(2, 1)

        graphs = model.sample(num_samples=2, batch_size=2, task_embedding=task_embeddings)

        self.assertEqual(len(graphs), 2)
        self.assertTrue(all(graph.number_of_nodes() > 0 for graph in graphs))


if __name__ == "__main__":
    unittest.main()
