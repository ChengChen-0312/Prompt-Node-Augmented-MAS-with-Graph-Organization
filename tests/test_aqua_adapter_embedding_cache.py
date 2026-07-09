import unittest
from unittest import mock

import numpy as np

from experiment.aqua import aqua_adapter


class AquaAdapterEmbeddingCacheTests(unittest.TestCase):
    def setUp(self):
        aqua_adapter._SENTENCE_EMBEDDING_MODEL = None

    def tearDown(self):
        aqua_adapter._SENTENCE_EMBEDDING_MODEL = None

    def test_get_sentence_embedding_reuses_default_encoder(self):
        class FakeSentenceTransformer:
            init_count = 0

            def __init__(self, model_name):
                FakeSentenceTransformer.init_count += 1
                self.model_name = model_name

            def encode(self, sentence):
                return np.array([len(sentence)], dtype=np.float32)

        with mock.patch.object(aqua_adapter, "SentenceTransformer", FakeSentenceTransformer):
            first = aqua_adapter.get_sentence_embedding("first")
            second = aqua_adapter.get_sentence_embedding("second")

        self.assertEqual(FakeSentenceTransformer.init_count, 1)
        self.assertEqual(first.tolist(), [5.0])
        self.assertEqual(second.tolist(), [6.0])


if __name__ == "__main__":
    unittest.main()
