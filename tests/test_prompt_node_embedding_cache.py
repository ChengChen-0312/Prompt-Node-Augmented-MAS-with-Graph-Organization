import os
import pickle
import tempfile
import unittest

import numpy as np


class FakeEncoder:
    def encode(self, text):
        seed = sum(ord(ch) for ch in text) % 17
        return np.full((4,), seed, dtype=float)


class PromptNodeEmbeddingCacheTests(unittest.TestCase):
    def test_aqua_adapter_backfills_missing_prompt_node_role_embeddings(self):
        from experiment.aqua.aqua_adapter import ensure_role_embeddings
        from experiment.aqua.prompt_node_graph import PN_ROLES

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = os.path.join(tmpdir, "precomputed_role_embeddings.pkl")
            with open(cache_path, "wb") as handle:
                pickle.dump({"Math Solver": np.ones((4,), dtype=float)}, handle)

            embeddings = ensure_role_embeddings(cache_path, encoder=FakeEncoder())

            for role in PN_ROLES:
                self.assertIn(role, embeddings)
            with open(cache_path, "rb") as handle:
                persisted = pickle.load(handle)
            for role in PN_ROLES:
                self.assertIn(role, persisted)


if __name__ == "__main__":
    unittest.main()
