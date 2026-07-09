import os
import subprocess
import sys
import tempfile
import unittest

import torch


FORBIDDEN_PT_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
}


def _policy_row(label=1, task_id="task_x"):
    return {
        "task_id": task_id,
        "slice_prefix": "synthetic",
        "candidate_method": "candidate",
        "policy_input": {
            "question": "Synthetic AQuA question?",
            "candidate_method": "candidate",
        },
        "graph_policy_target": {
            "candidate_label": label,
            "training_target": "preferred_graph" if label else "non_preferred_graph",
            "objective_reward": 10 if label else 2,
            "roles": ["Math Solver", "Programming Expert", "PN_Memory", "PN_Verifier", "PN_Router"],
            "edges": [[0, 1], [0, 2], [1, 2], [2, 3], [3, 4]],
            "prompt_node_roles": ["PN_Memory", "PN_Verifier", "PN_Router"],
            "prompt_node_role_counts": {"PN_Memory": 1, "PN_Verifier": 1, "PN_Router": 1},
            "prompt_node_specs": [
                {
                    "node_index": 2,
                    "role": "PN_Memory",
                    "identity_type": "Memory",
                    "runtime_behavior": "shared_state",
                    "permissions": ["read", "write"],
                    "budget": {"max_tokens": 256},
                    "lifecycle_actions": ["update", "compress"],
                },
                {
                    "node_index": 3,
                    "role": "PN_Verifier",
                    "identity_type": "Instruction/Verifier",
                    "runtime_behavior": "verify",
                    "permissions": ["read", "forward"],
                    "budget": {"max_tokens": 384},
                    "lifecycle_actions": ["update", "prune"],
                },
                {
                    "node_index": 4,
                    "role": "PN_Router",
                    "identity_type": "Agent-like",
                    "runtime_behavior": "Router",
                    "permissions": ["read", "forward"],
                    "budget": {"max_tokens": 256},
                    "lifecycle_actions": ["merge", "prune"],
                },
            ],
            "prompt_node_edge_permissions": {
                "PN_Memory->PN_Verifier": ["read", "write"],
                "PN_Verifier->PN_Router": ["read", "forward"],
            },
            "graph_signature": "synthetic",
        },
    }


class GraphPolicyPtExportTests(unittest.TestCase):
    def test_policy_target_to_networkx_graph_preserves_promptnode_roles_and_edges(self):
        from experiment.aqua.graph_policy_pt_export import policy_target_to_networkx_graph

        graph = policy_target_to_networkx_graph(_policy_row()["graph_policy_target"])

        roles = [data["role"] for _, data in graph.nodes(data=True)]
        self.assertEqual(roles[-3:], ["PN_Memory", "PN_Verifier", "PN_Router"])
        self.assertIn((2, 3), graph.edges())
        self.assertIn((3, 4), graph.edges())
        self.assertTrue(graph.graph["is_graph_policy_target"])
        self.assertEqual(graph.graph["prompt_node_specs"][2]["identity_type"], "Memory")
        self.assertEqual(graph.graph["prompt_node_specs"][4]["runtime_behavior"], "Router")
        self.assertIn("PN_Verifier->PN_Router", graph.graph["prompt_node_edge_permissions"])
        for field in FORBIDDEN_PT_FIELDS:
            self.assertNotIn(field, graph.graph)

    def test_export_positive_policy_rows_writes_pyg_files_without_answer_fields(self):
        from experiment.aqua.graph_policy_pt_export import export_positive_policy_pt_dataset

        rows = [_policy_row(label=1, task_id="task_pos"), _policy_row(label=0, task_id="task_neg")]
        with tempfile.TemporaryDirectory() as tmpdir:
            exported, summary = export_positive_policy_pt_dataset(rows, tmpdir)
            self.assertEqual(summary["source_policy_rows"], 2)
            self.assertEqual(summary["exported_pt_files"], 1)
            self.assertEqual(summary["skipped_non_positive_rows"], 1)
            self.assertEqual(summary["promptnode_spec_pt_files"], 1)
            self.assertEqual(summary["promptnode_edge_permission_pt_files"], 1)
            self.assertEqual(summary["outcome_field_violations"], 0)
            self.assertEqual(len(exported), 1)
            self.assertTrue(os.path.exists(exported[0]["path"]))

            pyg = torch.load(exported[0]["path"], weights_only=False)
            roles = [node["role"] for node in pyg.x]
            self.assertIn("PN_Memory", roles)
            self.assertIn("PN_Verifier", roles)
            self.assertIn("PN_Router", roles)
            self.assertEqual(pyg.question, "Synthetic AQuA question?")
            self.assertEqual(pyg.task, "Synthetic AQuA question?")
            self.assertEqual(pyg.prompt_node_specs[0]["identity_type"], "Memory")
            self.assertIn("PN_Verifier->PN_Router", pyg.prompt_node_edge_permissions)
            for field in FORBIDDEN_PT_FIELDS:
                self.assertFalse(hasattr(pyg, field))

    def test_real_r052_rows_export_to_aqua_graph_dataset_loadable_pt_files(self):
        from experiment.aqua.aqua_adapter import AquaGraphDataset
        from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows
        from experiment.aqua.graph_policy_pt_export import export_positive_policy_pt_dataset

        rows = load_jsonl_rows("experiment/aqua/aqua_first200_graph_policy_distill_rows.jsonl")
        with tempfile.TemporaryDirectory() as tmpdir:
            _, summary = export_positive_policy_pt_dataset(rows, tmpdir)
            dataset = AquaGraphDataset(
                data_dir="experiment/ColdStartData_Aqua",
                data_dir_ef=tmpdir,
                sample_size=5,
                pretrain=False,
            )

            self.assertEqual(summary["exported_pt_files"], 76)
            self.assertEqual(summary["promptnode_pt_files"], 76)
            self.assertEqual(summary["promptnode_spec_pt_files"], 76)
            self.assertEqual(summary["promptnode_edge_permission_pt_files"], 76)
            self.assertEqual(summary["outcome_field_violations"], 0)
            self.assertEqual(len(dataset), 5)
            roles = [data["role"] for _, data in dataset[0].nodes(data=True)]
            self.assertTrue({"PN_Memory", "PN_Verifier", "PN_Router"}.issubset(set(roles)))
            self.assertTrue(dataset[0].graph.get("task_embedding") is not None)

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/graph_policy_pt_export.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
