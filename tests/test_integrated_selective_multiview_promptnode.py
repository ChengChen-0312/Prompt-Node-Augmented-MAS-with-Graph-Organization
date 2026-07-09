import subprocess
import sys
import unittest


def _baseline_record(task_id="task_x", prediction="A", true_answer="B", votes=None):
    votes = votes if votes is not None else ["A"]
    return {
        "task_id": task_id,
        "question": "q",
        "true_answer": true_answer,
        "predicted_answer": prediction,
        "raw_response": f"The answer is {prediction}",
        "is_solved": prediction == true_answer,
        "agent_outputs": [
            {"node": index, "role": "Math Solver", "outputs": [f"The answer is {vote}"]}
            for index, vote in enumerate(votes)
        ],
    }


def _view_record(
    task_id="task_x",
    prediction="B",
    router_option="B",
    direct_votes=None,
    true_answer="B",
):
    direct_votes = direct_votes if direct_votes is not None else [router_option, router_option]
    return {
        "task_id": task_id,
        "question": "q",
        "true_answer": true_answer,
        "predicted_answer": prediction,
        "raw_response": f"The answer is {prediction}",
        "is_solved": prediction == true_answer,
        "generated_graph": {
            "roles": ["Math Solver", "Math Solver", "PN_Memory", "PN_Verifier", "PN_Router"],
            "edges": [[0, 2], [1, 2], [2, 3], [3, 4]],
        },
        "agent_outputs": [
            {"node": index, "role": "Math Solver", "outputs": [f"The answer is {vote}"]}
            for index, vote in enumerate(direct_votes)
        ]
        + [
            {
                "node": 9,
                "role": "PN_Router",
                "outputs": [
                    f"SUPPORTED_OPTION: {router_option}\n"
                    "BINDING_STATUS: EXACT_MATCH\n"
                    "FINAL_EVIDENCE_SUMMARY: verified option binding"
                ],
            }
        ],
    }


class IntegratedSelectiveMultiviewPromptNodeTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/evaluate_selective_multiview_promptnode.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rank_runtime_variants_scores_contracts_without_labels(self):
        from experiment.aqua.evaluate_selective_multiview_promptnode import rank_runtime_variants

        ranked = rank_runtime_variants(
            {
                "router": _view_record(router_option="B", direct_votes=["B", "B"]),
                "candidate": _view_record(prediction="C", router_option="C", direct_votes=["A", "A"]),
            }
        )

        self.assertEqual(ranked[0]["method_key"], "router")
        self.assertEqual(ranked[0]["router_option"], "B")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])
        self.assertNotIn("true_answer", ranked[0])
        self.assertNotIn("is_solved", ranked[0])

    def test_skips_multiview_when_baseline_trace_has_no_trigger(self):
        from experiment.aqua.evaluate_selective_multiview_promptnode import run_task_selective_multiview

        calls = []

        def baseline_runner(task):
            return _baseline_record(task["task_id"], prediction="C", true_answer="C", votes=["C", "C", "C"])

        def view_runner(task, view_config):
            calls.append(view_config["method_key"])
            return _view_record(task["task_id"])

        record = run_task_selective_multiview(
            {"task_id": "task_skip", "task": "q", "answer": "C"},
            baseline_runner,
            view_runner,
        )

        self.assertEqual(calls, [])
        self.assertFalse(record["multiview_was_run"])
        self.assertEqual(record["selected_source"], "baseline")
        self.assertEqual(record["predicted_answer"], "C")

    def test_runs_all_views_and_switches_on_unique_objective_top(self):
        from experiment.aqua.evaluate_selective_multiview_promptnode import (
            DEFAULT_VIEW_CONFIGS,
            run_task_selective_multiview,
        )

        calls = []

        def baseline_runner(task):
            record = _baseline_record(task["task_id"], prediction="A", true_answer="B", votes=["A"])
            record["agent_outputs"].append(
                {"node": 7, "role": "Programming Expert", "outputs": ["answer = 42"]}
            )
            return record

        def view_runner(task, view_config):
            calls.append(view_config["method_key"])
            if view_config["method_key"] == "router":
                return _view_record(task["task_id"], prediction="B", router_option="B", direct_votes=["B", "B"])
            return _view_record(task["task_id"], prediction="C", router_option="C", direct_votes=["A"])

        record = run_task_selective_multiview(
            {"task_id": "task_fix", "task": "q", "answer": "B"},
            baseline_runner,
            view_runner,
        )

        self.assertEqual(calls, [config["method_key"] for config in DEFAULT_VIEW_CONFIGS])
        self.assertTrue(record["multiview_was_run"])
        self.assertEqual(record["selected_source"], "objective_top")
        self.assertEqual(record["selected_method"], "router")
        self.assertEqual(record["predicted_answer"], "B")
        self.assertTrue(record["is_solved"])
        self.assertNotIn("true_answer", record["trigger_features"])
        self.assertNotIn("task_id", record["trigger_features"])

    def test_summarize_integrated_multiview_counts_cost_and_switches(self):
        from experiment.aqua.evaluate_selective_multiview_promptnode import summarize_integrated_multiview_records

        summary = summarize_integrated_multiview_records(
            [
                {
                    "task_id": "task_fix",
                    "is_solved": True,
                    "baseline_is_solved": False,
                    "multiview_was_run": True,
                    "selected_source": "objective_top",
                },
                {
                    "task_id": "task_keep",
                    "is_solved": True,
                    "baseline_is_solved": True,
                    "multiview_was_run": False,
                    "selected_source": "baseline",
                },
            ]
        )

        self.assertEqual(summary["overall"], "2/2")
        self.assertEqual(summary["baseline"], "1/2")
        self.assertEqual(summary["multiview_run"], "1/2")
        self.assertEqual(summary["fix_harm"], "1/0")
        self.assertEqual(summary["switch_tasks"], ["task_fix"])


if __name__ == "__main__":
    unittest.main()
