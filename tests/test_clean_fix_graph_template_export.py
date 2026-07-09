import subprocess
import sys
import unittest


def _row(signature="sig_a", task_id="task_a", target_class="clean_fix_preserve_graph"):
    return {
        "source_task_id": task_id,
        "source_slice_prefix": "synthetic",
        "source_candidate_method": "candidate",
        "clean_fix_distillation_target": {
            "target_class": target_class,
            "graph_policy_target": {
                "graph_signature": signature,
                "roles": ["Math Solver", "PN_Memory", "PN_Verifier", "PN_Router"],
                "edges": [[0, 1], [1, 2], [2, 3]],
                "prompt_node_specs": [
                    {"role": "PN_Memory", "identity_type": "Memory"},
                    {"role": "PN_Verifier", "identity_type": "Instruction/Verifier"},
                    {"role": "PN_Router", "identity_type": "Agent-like"},
                ],
                "prompt_node_edge_permissions": {
                    "Math Solver->PN_Memory": ["write"],
                    "PN_Memory->PN_Verifier": ["read"],
                    "PN_Verifier->PN_Router": ["read", "forward"],
                },
            },
        },
    }


class CleanFixGraphTemplateExportTests(unittest.TestCase):
    def test_build_templates_groups_positive_rows_and_keeps_update2_metadata(self):
        from experiment.aqua.clean_fix_graph_template_export import build_graph_templates

        templates, summary = build_graph_templates(
            [_row("sig_a", "task_a"), _row("sig_a", "task_b"), _row("sig_b", "task_c")]
        )

        self.assertEqual(summary["positive_rows"], 3)
        self.assertEqual(summary["unique_templates"], 2)
        self.assertEqual(templates[0]["support_count"], 2)
        self.assertEqual(templates[0]["graph_signature"], "sig_a")
        self.assertEqual(templates[0]["prompt_node_spec_count"], 3)
        self.assertIn("PN_Verifier->PN_Router", templates[0]["prompt_node_edge_permissions"])

    def test_real_r077_templates_are_promptnode_complete_and_leakage_free(self):
        from experiment.aqua.clean_fix_graph_template_export import build_first200_templates

        templates, summary = build_first200_templates()

        self.assertEqual(summary["source_rows"], 800)
        self.assertEqual(summary["positive_rows"], 76)
        self.assertEqual(summary["unique_templates"], 17)
        self.assertEqual(summary["templates_with_promptnode_specs"], 17)
        self.assertEqual(summary["templates_with_edge_permissions"], 17)
        self.assertEqual(summary["forbidden_field_violations"], 0)
        self.assertTrue(all(template["prompt_node_spec_count"] > 0 for template in templates))

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/clean_fix_graph_template_export.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
