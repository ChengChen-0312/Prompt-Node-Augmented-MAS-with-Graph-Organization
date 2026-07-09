import os
import pickle
import tempfile
import unittest

import torch

from experiment.args import Args


class TestARGDesignerMissingRoleEmbedding(unittest.TestCase):
    def test_model_initializes_when_role_embedding_is_missing(self):
        from experiment.model import ARGDesigner

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "precomputed_role_embeddings.pkl"), "wb") as f:
                pickle.dump({"Known": torch.zeros(384)}, f)

            args = Args().update_args()
            args.data_dir = tmp
            args.device = "cpu"
            args.role_mapping = {"Known": 0, "PN_Memory": 1}
            args.id_to_role = {0: "Known", 1: "PN_Memory"}
            args.START_TOKEN_ID = 2
            args.END_TOKEN_ID = 3

            model = ARGDesigner(
                args,
                {
                    "num_node_labels": 4,
                    "num_edge_labels": 1,
                    "max_num_nodes": 3,
                    "min_num_nodes": 1,
                    "max_num_edges": 2,
                    "min_num_edges": 0,
                    "is_directed": True,
                },
            )

            self.assertEqual(tuple(model.full_embedding_matrix.shape), (4, 384))


if __name__ == "__main__":
    unittest.main()
