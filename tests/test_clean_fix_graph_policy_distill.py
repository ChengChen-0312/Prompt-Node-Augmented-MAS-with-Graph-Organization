import subprocess
import sys
import unittest


FORBIDDEN_SELECTOR_INPUT_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "task_id",
    "source_task_id",
}


def _policy_row(label=1, training_target="preferred_graph", margin=4, task_id="task_x"):
    return {
        "task_id": task_id,
        "slice_prefix": "synthetic",
        "candidate_method": "candidate",
        "policy_input": {
            "slice_prefix": "synthetic",
            "question": "Synthetic AQuA question?",
            "candidate_method": "candidate",
            "task_id": task_id,
        },
        "graph_policy_target": {
            "candidate_label": label,
            "training_target": training_target,
            "objective_reward": 10 if label else 2,
            "score_components": {
                "strong_contract": 4 if label else 0,
                "direct_agreement": 3 if label else 0,
                "direct_vote_support": 2,
                "prompt_node_graph": 1 if label else 0,
                "conflict_penalty": 0,
                "weak_contract_penalty": 0,
            },
            "score_margin_to_next": margin,
            "roles": ["Math Solver", "Programming Expert", "PN_Memory", "PN_Verifier", "PN_Router"],
            "edges": [[0, 1], [0, 2], [1, 2], [2, 3], [3, 4]],
            "prompt_node_roles": ["PN_Memory", "PN_Verifier", "PN_Router"] if label else [],
            "prompt_node_role_counts": {"PN_Memory": 1, "PN_Verifier": 1, "PN_Router": 1}
            if label
            else {},
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
            ]
            if label
            else [],
            "prompt_node_edge_permissions": {
                "PN_Memory->PN_Verifier": ["read"],
                "PN_Verifier->PN_Router": ["read", "forward"],
            }
            if label
            else {},
            "graph_signature": "synthetic",
            "predicted_answer": "C",
            "router_option": "C",
            "direct_majority": "C",
            "is_solved": True,
        },
    }


def _has_forbidden_key(value):
    if isinstance(value, dict):
        return any(
            key in FORBIDDEN_SELECTOR_INPUT_FIELDS or _has_forbidden_key(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_has_forbidden_key(child) for child in value)
    return False


class CleanFixGraphPolicyDistillTests(unittest.TestCase):
    def test_build_rows_excludes_selector_input_leakage_and_preserves_promptnode_specs(self):
        from experiment.aqua.clean_fix_graph_policy_distill import build_clean_fix_graph_policy_rows

        rows, summary = build_clean_fix_graph_policy_rows(
            [
                _policy_row(label=1, task_id="task_pos"),
                _policy_row(label=0, training_target="multi_view_tie", margin=None, task_id="task_tie"),
            ]
        )
        positive = rows[0]
        ambiguous = rows[1]

        self.assertEqual(summary["rows"], 2)
        self.assertEqual(summary["clean_fix_preserve_rows"], 1)
        self.assertEqual(summary["ambiguous_suppress_rows"], 1)
        self.assertEqual(summary["selector_input_violations"], 0)
        self.assertFalse(_has_forbidden_key(positive["selector_policy_input"]))
        self.assertEqual(
            positive["clean_fix_distillation_target"]["target_class"],
            "clean_fix_preserve_graph",
        )
        self.assertEqual(
            positive["clean_fix_distillation_target"]["teacher_policy"],
            "preserve_high_margin_promptnode_graph",
        )
        specs = positive["clean_fix_distillation_target"]["graph_policy_target"]["prompt_node_specs"]
        self.assertEqual({spec["identity_type"] for spec in specs}, {"Memory", "Instruction/Verifier", "Agent-like"})
        self.assertEqual(
            ambiguous["clean_fix_distillation_target"]["target_class"],
            "ambiguous_or_low_margin_suppress",
        )

    def test_real_first200_export_is_label_free_at_input_and_schema_only_from_tail34(self):
        from experiment.aqua.clean_fix_graph_policy_distill import build_first200_clean_fix_graph_policy_rows

        rows, summary = build_first200_clean_fix_graph_policy_rows()

        self.assertEqual(summary["source_policy_rows"], 800)
        self.assertEqual(summary["rows"], 800)
        self.assertEqual(summary["clean_fix_preserve_rows"], 76)
        self.assertEqual(summary["clean_fix_promptnode_spec_rows"], 76)
        self.assertEqual(summary["selector_input_violations"], 0)
        self.assertTrue(summary["tail34_evidence_used_as_schema_only"])
        self.assertTrue(all(not _has_forbidden_key(row["selector_policy_input"]) for row in rows))
        self.assertTrue(
            all(
                row["clean_fix_distillation_target"]["graph_policy_target"]["prompt_node_specs"]
                for row in rows
                if row["clean_fix_distillation_target"]["target_class"] == "clean_fix_preserve_graph"
            )
        )

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/clean_fix_graph_policy_distill.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
