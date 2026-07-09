import tempfile
import unittest
from pathlib import Path

import torch
from torch_geometric.data import Data

from experiment.mmlu.export_promptedge_targets import (
    build_target_record,
    load_transfer_hashes,
    question_hash,
)


class TestR183MMLUPromptEdgeTargetExport(unittest.TestCase):
    def _make_graph(self, question: str) -> Data:
        data = Data()
        data.x = [
            {"role": "Knowlegable Expert", "constraint": "expert"},
            {"role": "Critic", "constraint": "critic"},
        ]
        data.edge_index = torch.tensor([[0], [1]], dtype=torch.long)
        data.num_nodes = 2
        data.question = question
        data.mode = "UnitTest"
        data.is_correct = True
        return data

    def test_question_hash_normalizes_whitespace(self):
        self.assertEqual(
            question_hash("What is 2 + 2?\nOption A: 3"),
            question_hash(" What  is 2 + 2? Option A: 3 "),
        )

    def test_transfer_hashes_filter_exact_heldout_questions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transfer_path = Path(tmpdir) / "transfer.jsonl"
            transfer_path.write_text(
                '{"question":"Held out?","task":"Held out?","answer":"A"}\n',
                encoding="utf-8",
            )
            transfer_hashes = load_transfer_hashes(str(transfer_path))

        record = build_target_record(
            source_path="heldout.pt",
            data=self._make_graph("Held out?"),
            transfer_hashes=transfer_hashes,
        )
        self.assertIsNone(record)

    def test_target_record_contains_promptedge_roles_and_permissions(self):
        record = build_target_record(
            source_path="train.pt",
            data=self._make_graph(
                "Train?\n"
                "Option A: yes\n"
                "Option B: no\n"
                "Option C: maybe\n"
                "Option D: unknown"
            ),
            transfer_hashes=set(),
        )

        self.assertIsNotNone(record)
        self.assertEqual(record["num_nodes_before"], 2)
        self.assertEqual(record["num_nodes_after"], 5)
        self.assertEqual(record["pn_roles"], ["PN_Memory", "PN_Verifier", "PN_Router"])
        self.assertIn("read", record["promptedge_permissions"])
        self.assertIn("write", record["promptedge_permissions"])
        self.assertIn("forward", record["promptedge_permissions"])
        self.assertTrue(record["leakage_checked_against_transfer100"])


if __name__ == "__main__":
    unittest.main()
