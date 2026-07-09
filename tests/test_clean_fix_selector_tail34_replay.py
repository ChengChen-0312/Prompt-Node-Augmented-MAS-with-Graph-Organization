import subprocess
import sys
import unittest


def _model():
    return {
        "weights": {
            "bias": -0.5,
            "objective_bucket_preferred_graph": 1.0,
            "num_prompt_nodes": 1.0,
            "has_promptnode_specs": 1.0,
            "has_promptnode_edge_permissions": 1.0,
        }
    }


def _record():
    return {
        "task_id": "task_x",
        "slice_prefix": "synthetic",
        "baseline_prediction": "A",
        "true_answer": "B",
        "ranked_variants": [
            {
                "method_key": "candidate",
                "method_index": 0,
                "score": 10,
                "score_components": {
                    "strong_contract": 4,
                    "direct_agreement": 3,
                    "direct_vote_support": 2,
                    "prompt_node_graph": 1,
                    "conflict_penalty": 0,
                    "weak_contract_penalty": 0,
                },
                "router_option": "B",
                "predicted_answer": "B",
                "generated_graph": {
                    "roles": ["Math Solver", "PN_Memory", "PN_Verifier", "PN_Router"],
                    "edges": [[0, 1], [1, 2], [2, 3]],
                },
            },
            {
                "method_key": "router",
                "method_index": 1,
                "score": 1,
                "score_components": {"direct_vote_support": 1},
                "router_option": None,
                "predicted_answer": "A",
            },
        ],
    }


class CleanFixSelectorTail34ReplayTests(unittest.TestCase):
    def test_selects_unique_positive_variant_when_graph_metadata_is_present(self):
        from experiment.aqua.clean_fix_selector_tail34_replay import select_record_prediction

        selected = select_record_prediction(_record(), _model())

        self.assertEqual(selected["predicted_answer"], "B")
        self.assertEqual(selected["selected_source"], "r078_clean_fix_selector")
        self.assertEqual(selected["selected_method"], "candidate")
        self.assertTrue(selected["selector_positive"])

    def test_real_tail34_replay_exposes_missing_promptnode_graph_metadata_boundary(self):
        from experiment.aqua.clean_fix_selector_tail34_replay import build_tail34_replay_payload

        records, summary = build_tail34_replay_payload()

        self.assertEqual(len(records), 34)
        self.assertEqual(summary["overall"]["overall"], "28/34")
        self.assertEqual(summary["overall"]["baseline"], "28/34")
        self.assertEqual(summary["overall"]["switches"], 0)
        self.assertEqual(summary["selector_feature_violations"], 0)
        self.assertEqual(summary["variants_with_promptnode_specs"], 0)
        self.assertEqual(summary["variants_with_explicit_promptnode_graph"], 0)
        self.assertIn("missing explicit PromptNode graph metadata", summary["claim_boundary"])

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/clean_fix_selector_tail34_replay.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
