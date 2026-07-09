import unittest
import tempfile

import networkx as nx


class R001SelectivePromptEdgePolicyTests(unittest.TestCase):
    def test_prompt_edge_metadata_assigns_expected_types(self):
        from experiment.aqua.prompt_node_graph import (
            attach_prompt_edge_metadata,
            summarize_prompt_edges,
        )

        graph = nx.DiGraph()
        graph.add_node(0, role="Math Solver")
        graph.add_node(1, role="Programming Expert")
        graph.add_node(2, role="PN_Memory")
        graph.add_node(3, role="PN_Verifier")
        graph.add_node(4, role="PN_Router")
        graph.add_edges_from([(0, 1), (0, 2), (1, 2), (2, 3), (3, 4)])

        annotated = attach_prompt_edge_metadata(graph)

        self.assertEqual(annotated.edges[0, 1]["prompt_edge_type"], "agent_flow")
        self.assertEqual(annotated.edges[0, 2]["prompt_edge_type"], "write_memory")
        self.assertEqual(annotated.edges[1, 2]["prompt_edge_type"], "write_memory")
        self.assertEqual(annotated.edges[2, 3]["prompt_edge_type"], "verify_contract")
        self.assertEqual(annotated.edges[3, 4]["prompt_edge_type"], "forward_verified")
        self.assertEqual(
            summarize_prompt_edges(annotated),
            {
                "agent_flow": 1,
                "write_memory": 2,
                "verify_contract": 1,
                "forward_verified": 1,
            },
        )

    def test_selective_export_marks_switch_rows_without_forbidden_fields(self):
        from experiment.aqua.r001_selective_promptedge_policy_export import (
            FORBIDDEN_SELECTOR_FIELDS,
            build_selective_promptedge_policy_rows,
        )

        r077_rows = [
            {
                "source_task_id": "task_a",
                "source_slice_prefix": "aqua_100",
                "source_candidate_method": "candidate",
                "selector_policy_input": {
                    "question": "Q?",
                    "candidate_method": "candidate",
                    "label_free_objective_features": {
                        "objective_bucket": "preferred_graph",
                        "score_margin_to_next": 5,
                    },
                    "candidate_graph_observation": {"num_prompt_nodes": 3},
                },
                "clean_fix_distillation_target": {
                    "target_class": "clean_fix_preserve_graph",
                    "graph_policy_target": {
                        "candidate_label": 1,
                        "training_target": "preferred_graph",
                        "objective_reward": 10,
                        "score_margin_to_next": 5,
                        "roles": [
                            "Math Solver",
                            "PN_Memory",
                            "PN_Verifier",
                            "PN_Router",
                        ],
                        "edges": [[0, 1], [1, 2], [2, 3]],
                        "prompt_node_edge_permissions": {
                            "PN_Verifier->PN_Router": ["forward"]
                        },
                    },
                },
            }
        ]
        r112_rows = [
            {
                "task_id": "task_a",
                "slice_prefix": "aqua_100",
                "policy_input": {
                    "objective_prediction_differs_from_baseline": True,
                    "baseline_direct_votes_split": True,
                    "objective_top_score": 8,
                },
                "target_action": "switch_to_objective",
            }
        ]

        rows, summary = build_selective_promptedge_policy_rows(r077_rows, r112_rows)

        self.assertEqual(summary["selective_insert_rows"], 1)
        self.assertEqual(rows[0]["selective_action"], "insert_promptnode_graph")
        self.assertEqual(rows[0]["graph_policy_target"]["candidate_label"], 1)
        self.assertIn("prompt_edge_type_counts", rows[0]["graph_policy_target"])
        serialized = str(rows[0])
        for field in FORBIDDEN_SELECTOR_FIELDS:
            self.assertNotIn(field, serialized)

    def test_real_r077_r112_export_creates_selective_pt_files(self):
        from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows
        from experiment.aqua.r001_selective_promptedge_policy_export import (
            build_selective_promptedge_policy_rows,
            export_selective_positive_pt_dataset,
        )

        r077 = load_jsonl_rows(
            "experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl"
        )
        r112 = load_jsonl_rows(
            "experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl"
        )
        rows, summary = build_selective_promptedge_policy_rows(r077, r112)
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest, pt_summary = export_selective_positive_pt_dataset(rows, tmpdir)

        self.assertEqual(summary["selector_input_forbidden_field_violations"], 0)
        self.assertGreater(summary["selective_insert_rows"], 0)
        self.assertEqual(len(manifest), pt_summary["exported_pt_files"])
        self.assertEqual(pt_summary["outcome_field_violations"], 0)
        self.assertEqual(
            pt_summary["promptnode_edge_permission_pt_files"],
            pt_summary["exported_pt_files"],
        )

    def test_r166_expanded_targets_separate_switch_and_preserve_safe(self):
        from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows
        from experiment.aqua.r166_expanded_selective_promptedge_targets import (
            build_expanded_selective_promptedge_targets,
            export_expanded_positive_pt_dataset,
        )

        r077 = load_jsonl_rows(
            "experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl"
        )
        r112 = load_jsonl_rows(
            "experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl"
        )
        rows, summary = build_expanded_selective_promptedge_targets(r077, r112)
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest, pt_summary = export_expanded_positive_pt_dataset(rows, tmpdir)

        self.assertEqual(summary["selector_input_forbidden_field_violations"], 0)
        self.assertEqual(summary["positive_graph_rows"], 76)
        self.assertEqual(summary["switch_critical_insert_rows"], 4)
        self.assertEqual(summary["preserve_safe_insert_rows"], 72)
        self.assertEqual(summary["suppress_or_fallback_rows"], 724)
        self.assertEqual(len(manifest), 76)
        self.assertEqual(pt_summary["exported_pt_files"], 76)
        self.assertEqual(pt_summary["promptnode_edge_permission_pt_files"], 76)


if __name__ == "__main__":
    unittest.main()
