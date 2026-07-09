import subprocess
import sys
import unittest


def _template(signature="sig_a", support=5):
    return {
        "graph_signature": signature,
        "support_count": support,
        "roles": ["Math Solver", "Programming Expert", "PN_Memory", "PN_Verifier", "PN_Router"],
        "edges": [[0, 1], [0, 2], [1, 2], [2, 3], [3, 4]],
        "prompt_node_roles": ["PN_Memory", "PN_Verifier", "PN_Router"],
        "prompt_node_specs": [
            {
                "node_index": 2,
                "role": "PN_Memory",
                "identity_type": "Memory",
                "permissions": ["read", "write"],
                "budget": {"max_tokens": 256, "max_updates": 3},
                "lifecycle_actions": ["update", "compress", "merge", "prune"],
            },
            {
                "node_index": 3,
                "role": "PN_Verifier",
                "identity_type": "Instruction/Verifier",
                "permissions": ["read", "write", "forward"],
                "budget": {"max_tokens": 384, "max_updates": 2},
                "lifecycle_actions": ["update", "prune", "upgrade"],
            },
            {
                "node_index": 4,
                "role": "PN_Router",
                "identity_type": "Agent-like",
                "permissions": ["read", "forward"],
                "budget": {"max_tokens": 256, "max_updates": 2},
                "lifecycle_actions": ["update", "merge", "prune"],
            },
        ],
        "prompt_node_edge_permissions": {
            "Math Solver->PN_Memory": ["write"],
            "Programming Expert->PN_Memory": ["write"],
            "PN_Memory->PN_Verifier": ["read"],
            "PN_Verifier->PN_Router": ["read", "forward"],
        },
        "support_slice_counts": {"aqua_100": support},
        "support_candidate_method_counts": {"candidate": support},
    }


class Tail34TemplateCandidateMaterializeTests(unittest.TestCase):
    def test_materializes_top_k_promptnode_templates_for_each_task(self):
        from experiment.aqua.tail34_template_candidate_materialize import (
            build_tail34_template_candidates,
        )

        rows, summary = build_tail34_template_candidates(
            templates=[_template("sig_low", 2), _template("sig_high", 9)],
            task_indices=[114, 56],
            top_k=1,
        )

        self.assertEqual(summary["num_tasks"], 2)
        self.assertEqual(summary["top_k"], 1)
        self.assertEqual(summary["total_candidates"], 2)
        self.assertEqual([row["task_id"] for row in rows], ["task_114", "task_56"])
        self.assertEqual(rows[0]["candidates"][0]["graph_signature"], "sig_high")
        self.assertEqual(rows[0]["candidates"][0]["rank"], 1)
        self.assertEqual(rows[0]["candidates"][0]["decision_exposure_policy"], "terminal")

    def test_candidate_records_are_executable_ready_and_update2_complete(self):
        from experiment.aqua.tail34_template_candidate_materialize import (
            build_tail34_template_candidates,
            template_to_executable_record,
        )

        candidate = template_to_executable_record(_template(), rank=1)

        roles = candidate["graph"]["roles"]
        self.assertEqual(roles[2:], ["PN_Memory", "PN_Verifier", "PN_Router"])
        self.assertEqual(candidate["graph"]["edges"], [[0, 1], [0, 2], [1, 2], [2, 3], [3, 4]])
        self.assertEqual(candidate["graph"]["edge_permissions"]["PN_Verifier->PN_Router"], ["read", "forward"])
        self.assertEqual(
            {spec["identity_type"] for spec in candidate["prompt_node_specs"]},
            {"Memory", "Instruction/Verifier", "Agent-like"},
        )
        self.assertTrue(all(spec.get("budget") for spec in candidate["prompt_node_specs"]))
        self.assertTrue(all(spec.get("lifecycle_actions") for spec in candidate["prompt_node_specs"]))

        _, summary = build_tail34_template_candidates([_template()], task_indices=[114], top_k=1)
        self.assertEqual(summary["templates_with_full_promptnode_specs"], 1)
        self.assertEqual(summary["templates_with_full_edge_permissions"], 1)

    def test_real_r082_tail34_candidate_pool_is_leakage_free(self):
        from experiment.aqua.tail34_template_candidate_materialize import (
            FORBIDDEN_RUNTIME_FIELDS,
            build_tail34_candidates_from_files,
            record_has_forbidden_field,
        )

        rows, summary = build_tail34_candidates_from_files(top_k=5)

        self.assertEqual(summary["num_tasks"], 34)
        self.assertEqual(summary["template_source_count"], 17)
        self.assertEqual(summary["total_candidates"], 170)
        self.assertEqual(summary["forbidden_field_violations"], 0)
        self.assertTrue(all(len(row["candidates"]) == 5 for row in rows))
        self.assertFalse(any(record_has_forbidden_field(row, FORBIDDEN_RUNTIME_FIELDS) for row in rows))

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/tail34_template_candidate_materialize.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
