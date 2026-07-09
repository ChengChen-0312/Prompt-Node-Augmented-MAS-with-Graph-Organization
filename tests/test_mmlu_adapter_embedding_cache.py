import unittest
from unittest import mock

import numpy as np

from experiment.mmlu import mmlu_adapter


class MMLUAdapterEmbeddingCacheTests(unittest.TestCase):
    def setUp(self):
        mmlu_adapter._SENTENCE_EMBEDDING_MODEL = None

    def tearDown(self):
        mmlu_adapter._SENTENCE_EMBEDDING_MODEL = None

    def test_get_sentence_embedding_reuses_default_encoder(self):
        class FakeSentenceTransformer:
            init_count = 0

            def __init__(self, model_name):
                FakeSentenceTransformer.init_count += 1
                self.model_name = model_name

            def encode(self, sentence):
                return np.array([len(sentence)], dtype=np.float32)

        with mock.patch.object(mmlu_adapter, "SentenceTransformer", FakeSentenceTransformer):
            first = mmlu_adapter.get_sentence_embedding("first")
            second = mmlu_adapter.get_sentence_embedding("second")

        self.assertEqual(FakeSentenceTransformer.init_count, 1)
        self.assertEqual(first.tolist(), [5.0])
        self.assertEqual(second.tolist(), [6.0])


if __name__ == "__main__":
    unittest.main()
