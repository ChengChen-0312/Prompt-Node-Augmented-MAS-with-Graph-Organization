import json
import tempfile
import unittest
from pathlib import Path

import torch

from experiment.mmlu.r184_promptedge_training_dry_run import (
    materialize_manifest,
    record_to_pyg_data,
)


class TestR184MMLUPromptEdgeTrainingDryRun(unittest.TestCase):
    def _record(self):
        return {
            "question": "Q?\nOption A: a\nOption B: b\nOption C: c\nOption D: d",
            "roles": ["Knowlegable Expert", "Critic", "PN_Memory", "PN_Verifier", "PN_Router"],
            "edges": [[0, 1], [0, 2], [1, 2], [2, 3], [3, 4]],
            "promptedge_meta": [
                {"promptedge": False, "permission": "agent_to_agent"},
                {"promptedge": True, "permission": "read"},
                {"promptedge": True, "permission": "read"},
                {"promptedge": True, "permission": "write"},
                {"promptedge": True, "permission": "forward"},
            ],
            "target_kind": "promptedge_preserve_safe_insert",
            "source_graph_path": "source.pt",
            "source_question_hash": "abc",
            "is_correct": True,
            "mode": "UnitTest",
        }

    def test_record_to_pyg_data_preserves_promptnode_roles_and_metadata(self):
        data = record_to_pyg_data(self._record())

        self.assertEqual(data.num_nodes, 5)
        self.assertEqual([node["role"] for node in data.x][-3:], ["PN_Memory", "PN_Verifier", "PN_Router"])
        self.assertEqual(data.edge_index.shape[1], 5)
        self.assertEqual(data.promptedge_meta[-1]["permission"], "forward")
        self.assertTrue(data.is_correct)
        self.assertEqual(data.mode, "PromptEdgeTarget")

    def test_materialize_manifest_writes_true_pt_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "manifest.jsonl"
            out_dir = Path(tmpdir) / "pt"
            manifest.write_text(json.dumps(self._record()) + "\n", encoding="utf-8")

            summary = materialize_manifest(str(manifest), str(out_dir))

            files = list(out_dir.glob("*.pt"))
            self.assertEqual(summary["materialized_graphs"], 1)
            self.assertEqual(len(files), 1)
            self.assertIn("True", files[0].name)
            loaded = torch.load(files[0], map_location="cpu", weights_only=False)
            self.assertEqual(loaded.target_kind, "promptedge_preserve_safe_insert")


if __name__ == "__main__":
    unittest.main()
