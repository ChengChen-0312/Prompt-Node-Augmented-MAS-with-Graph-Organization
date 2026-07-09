import unittest

import torch
from torch_geometric.data import Data

from experiment.mmlu.export_promptedge_targets import build_target_record


class TestR211MMLURouterFinalSchema(unittest.TestCase):
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

    def test_target_record_contains_router_final_abstain_schema_without_leakage(self):
        record = build_target_record(
            source_path="train.pt",
            data=self._make_graph(
                "Which option is correct?\n"
                "Option A: alpha\n"
                "Option B: beta\n"
                "Option C: gamma\n"
                "Option D: delta"
            ),
            transfer_hashes=set(),
        )

        schema = record["router_final_schema"]
        self.assertEqual(schema["schema_version"], "r211_router_final_v1")
        self.assertEqual(schema["target_kind"], "router_final_or_abstain")
        self.assertEqual(schema["router_action"], "abstain")
        self.assertEqual(schema["target_option_label"], "NONE")
        self.assertEqual(schema["allowed_option_labels"], ["A", "B", "C", "D", "NONE"])
        self.assertFalse(schema["override_label"])
        self.assertFalse(schema["gold_answer_used"])
        self.assertTrue(schema["promptedge_text_policy"]["edge_text_as_prompt"])
        self.assertEqual(schema["edge_permission_labels"], ["read", "write", "forward"])

        forbidden = set(schema["forbidden_model_visible_fields"])
        self.assertIn("answer", forbidden)
        self.assertIn("true_answer", forbidden)
        self.assertIn("is_correct", forbidden)
        self.assertIn("task_id", forbidden)
        self.assertTrue(forbidden.isdisjoint(schema["model_visible_fields"]))

    def test_router_final_schema_uses_dynamic_option_labels_for_aqua_style_options(self):
        record = build_target_record(
            source_path="train.pt",
            data=self._make_graph(
                "Pick one. A) one B) two C) three D) four E) five"
            ),
            transfer_hashes=set(),
        )

        schema = record["router_final_schema"]
        self.assertEqual(schema["allowed_option_labels"], ["A", "B", "C", "D", "E", "NONE"])


if __name__ == "__main__":
    unittest.main()
