import subprocess
import sys
import unittest


def _baseline_record(task_id="task_x", prediction="B", votes=None, true_answer="D"):
    votes = votes or ["B", "D"]
    return {
        "task_id": task_id,
        "question": "q",
        "true_answer": true_answer,
        "predicted_answer": prediction,
        "raw_response": f"The answer is {prediction}",
        "is_solved": prediction == true_answer,
        "agent_outputs": [
            {"node": idx, "role": "Math Solver", "outputs": [f"The answer is {vote}"]}
            for idx, vote in enumerate(votes)
        ],
    }


def _promptnode_record(task_id="task_x", prediction="D", router_option="D", true_answer="D"):
    return {
        "task_id": task_id,
        "question": "q",
        "true_answer": true_answer,
        "predicted_answer": prediction,
        "raw_response": f"The answer is {prediction}",
        "is_solved": prediction == true_answer,
        "agent_outputs": [
            {"node": 0, "role": "Math Solver", "outputs": ["The answer is D"]},
            {
                "node": 1,
                "role": "PN_Router",
                "outputs": [
                    f"SUPPORTED_OPTION: {router_option}\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: verified"
                ],
            },
        ],
    }


class IntegratedSelectivePromptNodeEvalTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/evaluate_selective_promptnode.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_baseline_prefilter_blocks_direct_majority(self):
        from experiment.aqua.evaluate_selective_promptnode import baseline_prefilter_passes

        passed, features = baseline_prefilter_passes(
            _baseline_record(votes=["B", "B", "D"])
        )

        self.assertFalse(passed)
        self.assertEqual(features["direct_max_count"], 2)
        self.assertEqual(features["prefilter_block_reason"], "direct_majority")
        self.assertNotIn("true_answer", features)
        self.assertNotIn("task_id", features)

    def test_baseline_prefilter_passes_direct_conflict_without_majority(self):
        from experiment.aqua.evaluate_selective_promptnode import baseline_prefilter_passes

        passed, features = baseline_prefilter_passes(
            _baseline_record(votes=["B", "D"])
        )

        self.assertTrue(passed)
        self.assertEqual(features["direct_vote_counts"], {"B": 1, "D": 1})
        self.assertEqual(features["prefilter_block_reason"], "")

    def test_run_task_selective_skips_promptnode_when_prefilter_blocks(self):
        from experiment.aqua.evaluate_selective_promptnode import run_task_selective

        calls = {"pn": 0}

        def baseline_runner(task):
            return _baseline_record(task_id=task["task_id"], prediction="B", votes=["B", "B", "D"])

        def promptnode_runner(task):
            calls["pn"] += 1
            return _promptnode_record(task_id=task["task_id"])

        record = run_task_selective(
            {"task_id": "task_block", "task": "q", "answer": "B"},
            baseline_runner,
            promptnode_runner,
        )

        self.assertEqual(calls["pn"], 0)
        self.assertEqual(record["selected_source"], "baseline")
        self.assertFalse(record["promptnode_was_run"])
        self.assertEqual(record["predicted_answer"], "B")

    def test_run_task_selective_runs_promptnode_and_switches_when_gate_passes(self):
        from experiment.aqua.evaluate_selective_promptnode import run_task_selective

        calls = {"pn": 0}

        def baseline_runner(task):
            return _baseline_record(task_id=task["task_id"], prediction="B", votes=["B", "D"])

        def promptnode_runner(task):
            calls["pn"] += 1
            return _promptnode_record(task_id=task["task_id"], prediction="D", router_option="D")

        record = run_task_selective(
            {"task_id": "task_fix", "task": "q", "answer": "D"},
            baseline_runner,
            promptnode_runner,
        )

        self.assertEqual(calls["pn"], 1)
        self.assertTrue(record["promptnode_was_run"])
        self.assertEqual(record["selected_source"], "promptnode")
        self.assertEqual(record["predicted_answer"], "D")
        self.assertTrue(record["is_solved"])
        self.assertNotIn("true_answer", record["gate_features"])
        self.assertNotIn("is_solved", record["gate_features"])
        self.assertNotIn("task_id", record["gate_features"])

    def test_summarize_integrated_records_counts_pn_calls_and_switches(self):
        from experiment.aqua.evaluate_selective_promptnode import summarize_integrated_records

        records = [
            {
                "task_id": "task_fix",
                "true_answer": "D",
                "predicted_answer": "D",
                "is_solved": True,
                "baseline_prediction": "B",
                "promptnode_prediction": "D",
                "baseline_is_solved": False,
                "promptnode_is_solved": True,
                "selected_source": "promptnode",
                "promptnode_was_run": True,
            },
            {
                "task_id": "task_keep",
                "true_answer": "A",
                "predicted_answer": "A",
                "is_solved": True,
                "baseline_prediction": "A",
                "promptnode_prediction": None,
                "baseline_is_solved": True,
                "promptnode_is_solved": False,
                "selected_source": "baseline",
                "promptnode_was_run": False,
            },
        ]

        summary = summarize_integrated_records(records)

        self.assertEqual(summary["solved_tasks"], 2)
        self.assertEqual(summary["promptnode_run_count"], 1)
        self.assertEqual(summary["promptnode_switch_count"], 1)
        self.assertEqual(summary["fixes_vs_baseline"], 1)
        self.assertEqual(summary["harms_vs_baseline"], 0)

    def test_prepare_runtime_paths_absolutizes_outputs_before_chdir(self):
        from argparse import Namespace

        from experiment.aqua.evaluate_selective_promptnode import prepare_runtime_paths

        args = Namespace(
            baseline_model_path="experiment/aqua/output/base",
            promptnode_model_path="experiment/aqua/output/pn",
            dataset_path="datasets/AQuA/AQuA.jsonl",
            task_split_path="experiment/aqua/task_split_aqua_tail34.json",
            output_file="experiment/aqua/out.jsonl",
            summary_json="experiment/aqua/summary.json",
            summary_log_file="experiment/aqua/summary.jsonl",
            report_md="experiment/aqua/report.md",
        )

        prepare_runtime_paths(args, repo_root="/repo", aqua_dir="/repo/experiment/aqua")

        self.assertEqual(args.runtime_cwd, "/repo/experiment/aqua")
        self.assertEqual(args.baseline_model_path, "/repo/experiment/aqua/output/base")
        self.assertEqual(args.promptnode_model_path, "/repo/experiment/aqua/output/pn")
        self.assertEqual(args.dataset_path, "/repo/datasets/AQuA/AQuA.jsonl")
        self.assertEqual(args.output_file, "/repo/experiment/aqua/out.jsonl")

    def test_infer_model_workdir_handles_legacy_and_graph_policy_configs(self):
        from experiment.aqua.evaluate_selective_promptnode import (
            AQUA_DIR,
            REPO_ROOT,
            infer_model_workdir,
        )

        baseline_dir = (
            f"{REPO_ROOT}/experiment/aqua/output/aqua_sync20_model_20260707-230509"
        )
        promptnode_dir = (
            f"{REPO_ROOT}/experiment/aqua/output/aqua_pn_graph_policy_r055_full"
        )

        self.assertEqual(infer_model_workdir(baseline_dir), AQUA_DIR)
        self.assertEqual(infer_model_workdir(promptnode_dir), REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
