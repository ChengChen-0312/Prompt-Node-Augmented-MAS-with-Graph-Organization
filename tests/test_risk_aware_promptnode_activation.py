import subprocess
import sys
import unittest


def _baseline_record(prediction="B", votes=None, true_answer="D"):
    votes = votes if votes is not None else ["A", "D"]
    return {
        "task_id": "task_x",
        "question": "q",
        "true_answer": true_answer,
        "predicted_answer": prediction,
        "is_solved": prediction == true_answer,
        "agent_outputs": [
            {"node": idx, "role": "Math Solver", "outputs": [f"The answer is {vote}"]}
            for idx, vote in enumerate(votes)
        ],
    }


def _promptnode_record(prediction="D", router_option="D", status="EXACT_MATCH"):
    return {
        "task_id": "task_x",
        "question": "q",
        "true_answer": "D",
        "predicted_answer": prediction,
        "agent_outputs": [
            {"node": 0, "role": "Math Solver", "outputs": [f"The answer is {prediction}"]},
            {
                "node": 1,
                "role": "PN_Router",
                "outputs": [
                    f"SUPPORTED_OPTION: {router_option}\n"
                    f"BINDING_STATUS: {status}\n"
                    "FINAL_EVIDENCE_SUMMARY: verified"
                ],
            },
        ],
    }


class RiskAwarePromptNodeActivationTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/risk_aware_promptnode_activation.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_extract_baseline_risk_features_excludes_outcome_fields(self):
        from experiment.aqua.risk_aware_promptnode_activation import (
            extract_baseline_risk_features,
        )

        features = extract_baseline_risk_features(
            _baseline_record(prediction="E", votes=["A", "A"], true_answer="E")
        )

        self.assertEqual(features["baseline_prediction"], "E")
        self.assertEqual(features["direct_vote_counts"], {"A": 2})
        self.assertTrue(features["final_direct_mismatch"])
        self.assertFalse(features["direct_conflict"])
        self.assertNotIn("true_answer", features)
        self.assertNotIn("is_solved", features)
        self.assertNotIn("task_id", features)

    def test_should_run_promptnode_r063_expands_beyond_direct_conflict(self):
        from experiment.aqua.risk_aware_promptnode_activation import (
            extract_baseline_risk_features,
            should_run_promptnode_r063,
        )

        mismatch_features = extract_baseline_risk_features(
            _baseline_record(prediction="E", votes=["A", "A"])
        )
        majority_features = extract_baseline_risk_features(
            _baseline_record(prediction="A", votes=["A", "A", "A"])
        )

        self.assertTrue(should_run_promptnode_r063(mismatch_features))
        self.assertFalse(should_run_promptnode_r063(majority_features))

    def test_select_promptnode_requires_strong_compatible_router(self):
        from experiment.aqua.risk_aware_promptnode_activation import (
            extract_baseline_risk_features,
            should_select_promptnode_r063,
        )

        base = _baseline_record(prediction="B", votes=["B", "D"])
        features = extract_baseline_risk_features(base)

        selected, selected_features = should_select_promptnode_r063(
            base,
            _promptnode_record(prediction="D", router_option="D", status="EXACT_MATCH"),
            features,
        )
        rejected, rejected_features = should_select_promptnode_r063(
            base,
            _promptnode_record(prediction="C", router_option="C", status="EXACT_MATCH"),
            features,
        )

        self.assertTrue(selected)
        self.assertEqual(selected_features["selection_reason"], "strong_router_resolves_conflict")
        self.assertFalse(rejected)
        self.assertEqual(rejected_features["selection_block_reason"], "router_not_compatible")

    def test_build_r063_replay_records_counts_runs_and_switches(self):
        from experiment.aqua.risk_aware_promptnode_activation import (
            build_r063_replay_records,
            summarize_r063_records,
        )

        baseline_records = {
            "task_fix": _baseline_record(prediction="B", votes=["B", "D"], true_answer="D"),
            "task_keep": _baseline_record(prediction="A", votes=["A", "A"], true_answer="A"),
        }
        baseline_records["task_fix"]["task_id"] = "task_fix"
        baseline_records["task_keep"]["task_id"] = "task_keep"

        promptnode_records = {
            "task_fix": _promptnode_record(prediction="D", router_option="D"),
            "task_keep": _promptnode_record(prediction="B", router_option="B"),
        }

        records = build_r063_replay_records(baseline_records, promptnode_records)
        summary = summarize_r063_records(records)
        by_task = {record["task_id"]: record for record in records}

        self.assertEqual(by_task["task_fix"]["selected_source"], "promptnode")
        self.assertEqual(by_task["task_keep"]["selected_source"], "baseline")
        self.assertTrue(by_task["task_fix"]["promptnode_would_run"])
        self.assertFalse(by_task["task_keep"]["promptnode_would_run"])
        self.assertNotIn("true_answer", by_task["task_fix"]["risk_features"])
        self.assertEqual(summary["promptnode_run_count"], 1)
        self.assertEqual(summary["promptnode_switch_count"], 1)
        self.assertEqual(summary["fixes_vs_baseline"], 1)
        self.assertEqual(summary["harms_vs_baseline"], 0)


if __name__ == "__main__":
    unittest.main()
