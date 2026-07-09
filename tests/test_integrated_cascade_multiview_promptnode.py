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


def _view_record(task_id="task_x", prediction="B", true_answer="B"):
    return {
        "task_id": task_id,
        "question": "q",
        "true_answer": true_answer,
        "predicted_answer": prediction,
        "raw_response": f"The answer is {prediction}",
        "is_solved": prediction == true_answer,
        "generated_graph": {"roles": ["Math Solver", "Math Solver"], "edges": [[0, 1]]},
        "agent_outputs": [
            {"node": 0, "role": "Math Solver", "outputs": [f"The answer is {prediction}"]},
            {"node": 1, "role": "Math Solver", "outputs": [f"The answer is {prediction}"]},
        ],
    }


class IntegratedCascadeMultiviewPromptNodeTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/evaluate_cascade_multiview_promptnode.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_skips_views_when_baseline_trigger_does_not_fire(self):
        from experiment.aqua.evaluate_cascade_multiview_promptnode import run_task_cascade_multiview

        calls = []

        def baseline_runner(task):
            return _baseline_record(task["task_id"], prediction="C", true_answer="C", votes=["C", "C"])

        def view_runner(task, view_config):
            calls.append(view_config["method_key"])
            return _view_record(task["task_id"])

        record = run_task_cascade_multiview(
            {"task_id": "task_skip", "task": "q", "answer": "C"},
            baseline_runner,
            view_runner,
        )

        self.assertEqual(calls, [])
        self.assertEqual(record["selected_source"], "baseline")
        self.assertEqual(record["view_calls"], 0)
        self.assertFalse(record["multiview_was_run"])

    def test_early_accepts_valid_baseline_after_two_views(self):
        from experiment.aqua.evaluate_cascade_multiview_promptnode import (
            DEFAULT_CASCADE_VIEW_CONFIGS,
            run_task_cascade_multiview,
        )

        calls = []

        def baseline_runner(task):
            record = _baseline_record(task["task_id"], prediction="C", true_answer="C", votes=["C"])
            record["agent_outputs"].append(
                {"node": 7, "role": "Programming Expert", "outputs": ["answer = 42"]}
            )
            return record

        def view_runner(task, view_config):
            calls.append(view_config["method_key"])
            return _view_record(task["task_id"], prediction="C", true_answer="C")

        record = run_task_cascade_multiview(
            {"task_id": "task_keep", "task": "q", "answer": "C"},
            baseline_runner,
            view_runner,
        )

        self.assertEqual(calls, [config["method_key"] for config in DEFAULT_CASCADE_VIEW_CONFIGS[:2]])
        self.assertEqual(record["selected_source"], "baseline_early_accept")
        self.assertEqual(record["view_calls"], 2)
        self.assertEqual(record["predicted_answer"], "C")
        self.assertNotIn("true_answer", record["decision_features"])
        self.assertNotIn("is_solved", record["decision_features"])

    def test_invalid_baseline_switch_requires_three_view_support(self):
        from experiment.aqua.evaluate_cascade_multiview_promptnode import run_task_cascade_multiview

        calls = []

        def baseline_runner(task):
            return _baseline_record(task["task_id"], prediction=None, true_answer="A", votes=[])

        def view_runner(task, view_config):
            calls.append(view_config["method_key"])
            prediction = "A" if len(calls) <= 3 else "B"
            return _view_record(task["task_id"], prediction=prediction, true_answer="A")

        record = run_task_cascade_multiview(
            {"task_id": "task_fix", "task": "q", "answer": "A"},
            baseline_runner,
            view_runner,
        )

        self.assertEqual(calls, ["router", "conservative", "calibrated"])
        self.assertEqual(record["selected_source"], "cascade_objective")
        self.assertEqual(record["predicted_answer"], "A")
        self.assertEqual(record["view_calls"], 3)
        self.assertTrue(record["is_solved"])

    def test_surgical_trigger_policy_skips_missing_vote_with_strong_baseline_support(self):
        from experiment.aqua.evaluate_cascade_multiview_promptnode import run_task_cascade_multiview

        calls = []

        def baseline_runner(task):
            record = _baseline_record(task["task_id"], prediction="C", true_answer="C", votes=["C", "C"])
            record["agent_outputs"].append(
                {"node": 9, "role": "Math Solver", "outputs": ["I agree with the derivation."]}
            )
            return record

        def view_runner(task, view_config):
            calls.append(view_config["method_key"])
            return _view_record(task["task_id"], prediction="C", true_answer="C")

        record = run_task_cascade_multiview(
            {"task_id": "task_strong_missing_vote", "task": "q", "answer": "C"},
            baseline_runner,
            view_runner,
            trigger_policy="r073_surgical",
        )

        self.assertEqual(calls, [])
        self.assertEqual(record["selected_source"], "baseline")
        self.assertEqual(record["view_calls"], 0)
        self.assertFalse(record["multiview_was_run"])

    def test_summary_counts_view_calls_and_switches(self):
        from experiment.aqua.evaluate_cascade_multiview_promptnode import summarize_cascade_integrated_records

        summary = summarize_cascade_integrated_records(
            [
                {
                    "task_id": "task_fix",
                    "is_solved": True,
                    "baseline_is_solved": False,
                    "multiview_was_run": True,
                    "selected_source": "cascade_objective",
                    "view_calls": 3,
                    "full_view_count": 4,
                },
                {
                    "task_id": "task_keep",
                    "is_solved": True,
                    "baseline_is_solved": True,
                    "multiview_was_run": True,
                    "selected_source": "baseline_early_accept",
                    "view_calls": 2,
                    "full_view_count": 4,
                },
            ]
        )

        self.assertEqual(summary["overall"], "2/2")
        self.assertEqual(summary["baseline"], "1/2")
        self.assertEqual(summary["fix_harm"], "1/0")
        self.assertEqual(summary["view_calls"], "5/8")
        self.assertEqual(summary["switch_tasks"], ["task_fix"])


if __name__ == "__main__":
    unittest.main()
