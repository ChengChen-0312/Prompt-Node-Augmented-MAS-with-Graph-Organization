import subprocess
import sys
import unittest


class CleanFixSelectorR058ReplayTests(unittest.TestCase):
    def test_synthetic_metadata_candidate_can_be_scored_positive(self):
        from experiment.aqua.clean_fix_selector_r058_replay import build_candidate_selector_row
        from experiment.aqua.clean_fix_selector_ranker import predict_label

        model = {
            "weights": {
                "bias": -0.5,
                "objective_bucket_preferred_graph": 1.0,
                "num_prompt_nodes": 1.0,
                "has_promptnode_specs": 1.0,
                "has_promptnode_edge_permissions": 1.0,
            }
        }
        baseline = {
            "predicted_answer": "A",
            "agent_outputs": [{"role": "Math Solver", "outputs": ["The answer is A"]}],
        }
        promptnode = {
            "predicted_answer": "B",
            "generated_graph": {
                "roles": ["Math Solver", "PN_Memory", "PN_Verifier", "PN_Router"],
                "edges": [[0, 1], [1, 2], [2, 3]],
            },
            "agent_outputs": [
                {
                    "role": "PN_Router",
                    "outputs": ["SUPPORTED_OPTION: B\nBINDING_STATUS: EXACT_MATCH"],
                }
            ],
        }

        row = build_candidate_selector_row(baseline, promptnode)

        self.assertEqual(predict_label(model, row), 1)
        self.assertEqual(
            row["selector_policy_input"]["candidate_graph_observation"]["num_prompt_nodes"],
            3,
        )

    def test_real_r058_metadata_replay_is_negative_control(self):
        from experiment.aqua.clean_fix_selector_r058_replay import build_r058_replay_payload

        records, summary = build_r058_replay_payload()

        self.assertEqual(len(records), 34)
        self.assertEqual(summary["overall"]["overall"], "25/34")
        self.assertEqual(summary["overall"]["baseline"], "28/34")
        self.assertEqual(summary["overall"]["switches"], 3)
        self.assertEqual(summary["overall"]["fix_harm"], "0/3")
        self.assertEqual(summary["generated_promptnode_graph_records"], 34)
        self.assertEqual(summary["selector_feature_violations"], 0)
        self.assertIn("metadata alone is insufficient", summary["claim_boundary"])

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/clean_fix_selector_r058_replay.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
