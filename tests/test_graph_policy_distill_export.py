import subprocess
import sys
import unittest


FORBIDDEN_POLICY_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "r035_selected_prediction",
    "r035_selected_source",
}


def _training_row(task_id="task_x", method="candidate", target="preferred_graph"):
    return {
        "task_id": task_id,
        "slice_prefix": "synthetic",
        "candidate_method": method,
        "objective_score": 10 if target == "preferred_graph" else 2,
        "score_components": {"strong_contract": 4, "direct_agreement": 3},
        "score_margin_to_next": 4 if target == "preferred_graph" else None,
        "training_target": target,
        "router_option": "B",
        "direct_majority": "B",
        "predicted_answer": "B",
        "is_solved": True,
    }


def _result_record():
    return {
        "question": "How many minutes?",
        "true_answer": "B",
        "predicted_answer": "B",
        "is_solved": True,
        "generated_graph": {
            "roles": ["Math Solver", "Programming Expert", "PN_Memory", "PN_Verifier", "PN_Router"],
            "edges": [[0, 1], [0, 2], [1, 2], [2, 3], [3, 4]],
        },
    }


class GraphPolicyDistillExportTests(unittest.TestCase):
    def test_normalize_graph_builds_node_and_edge_supervision(self):
        from experiment.aqua.graph_policy_distill_export import normalize_graph_for_policy

        policy_graph = normalize_graph_for_policy(_result_record()["generated_graph"])

        self.assertEqual(policy_graph["roles"][2:], ["PN_Memory", "PN_Verifier", "PN_Router"])
        self.assertEqual(policy_graph["prompt_node_roles"], ["PN_Memory", "PN_Verifier", "PN_Router"])
        self.assertEqual(policy_graph["prompt_node_role_counts"]["PN_Router"], 1)
        self.assertIn("PN_Verifier->PN_Router", policy_graph["edge_role_pairs"])
        self.assertIn("PN_Verifier->PN_Router", policy_graph["prompt_node_edge_role_pairs"])
        self.assertIn("PN_Memory|PN_Router|PN_Verifier", policy_graph["graph_signature"])

    def test_prompt_node_specs_encode_update2_identity_permissions_and_lifecycle(self):
        from experiment.aqua.graph_policy_distill_export import normalize_graph_for_policy

        policy_graph = normalize_graph_for_policy(_result_record()["generated_graph"])
        specs = {spec["role"]: spec for spec in policy_graph["prompt_node_specs"]}

        self.assertEqual(specs["PN_Memory"]["identity_type"], "Memory")
        self.assertEqual(specs["PN_Verifier"]["identity_type"], "Instruction/Verifier")
        self.assertEqual(specs["PN_Router"]["identity_type"], "Agent-like")
        self.assertEqual(specs["PN_Router"]["runtime_behavior"], "Router")
        self.assertNotEqual(specs["PN_Router"]["identity_type"], "Router")
        self.assertIn("read", specs["PN_Memory"]["permissions"])
        self.assertIn("write", specs["PN_Memory"]["permissions"])
        self.assertIn("forward", specs["PN_Router"]["permissions"])
        self.assertIn("compress", specs["PN_Memory"]["lifecycle_actions"])
        self.assertIn("prune", specs["PN_Router"]["lifecycle_actions"])
        self.assertTrue(specs["PN_Verifier"]["budget"]["max_tokens"] > 0)
        self.assertIn("PN_Verifier->PN_Router", policy_graph["prompt_node_edge_permissions"])

    def test_build_policy_rows_excludes_answer_fields_and_marks_positive_target(self):
        from experiment.aqua.graph_policy_distill_export import build_policy_rows

        training_rows = [
            _training_row(target="preferred_graph"),
            _training_row(method="router", target="non_preferred_graph"),
        ]
        result_sets = {
            "candidate": {"task_x": _result_record()},
            "router": {
                "task_x": {
                    "question": "How many minutes?",
                    "generated_graph": {
                        "roles": ["Math Solver", "Programming Expert"],
                        "edges": [[0, 1]],
                    },
                }
            },
        }

        rows, summary = build_policy_rows(training_rows, result_sets)

        self.assertEqual(len(rows), 2)
        positive = rows[0]
        negative = rows[1]
        self.assertEqual(positive["graph_policy_target"]["candidate_label"], 1)
        self.assertEqual(negative["graph_policy_target"]["candidate_label"], 0)
        self.assertEqual(positive["graph_policy_target"]["training_target"], "preferred_graph")
        self.assertEqual(positive["graph_policy_target"]["prompt_node_role_counts"]["PN_Memory"], 1)
        self.assertIn("prompt_node_specs", positive["graph_policy_target"])
        self.assertIn("prompt_node_edge_permissions", positive["graph_policy_target"])
        self.assertNotIn("task_id", positive["policy_input"])
        self.assertFalse(FORBIDDEN_POLICY_FIELDS & set(positive))
        self.assertFalse(FORBIDDEN_POLICY_FIELDS & set(positive["policy_input"]))
        self.assertFalse(FORBIDDEN_POLICY_FIELDS & set(positive["graph_policy_target"]))
        self.assertEqual(summary["policy_rows"], 2)
        self.assertEqual(summary["positive_policy_rows"], 1)
        self.assertEqual(summary["positive_prompt_node_spec_rows"], 1)
        self.assertEqual(summary["positive_prompt_node_edge_permission_rows"], 1)
        self.assertEqual(summary["outcome_field_violations"], 0)

    def test_real_first200_policy_export_has_node_edge_targets_without_outcome_fields(self):
        from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows
        from experiment.aqua.graph_policy_distill_export import build_first200_policy_rows

        training_rows = load_jsonl_rows("experiment/aqua/aqua_first200_graph_objective_training_rows.jsonl")
        rows, summary = build_first200_policy_rows(training_rows, base_dir="experiment/aqua")

        self.assertEqual(summary["source_training_rows"], 800)
        self.assertEqual(summary["policy_rows"], 800)
        self.assertEqual(summary["positive_policy_rows"], 76)
        self.assertEqual(summary["positive_prompt_node_spec_rows"], 76)
        self.assertEqual(summary["positive_prompt_node_edge_permission_rows"], 76)
        self.assertEqual(summary["outcome_field_violations"], 0)
        self.assertGreater(summary["positive_prompt_node_policy_rows"], 0)
        self.assertTrue(all("graph_policy_target" in row for row in rows))
        self.assertTrue(all(not (FORBIDDEN_POLICY_FIELDS & set(row)) for row in rows))

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/graph_policy_distill_export.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
