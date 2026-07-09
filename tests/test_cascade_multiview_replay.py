import subprocess
import sys
import unittest


def _record(
    task_id,
    baseline_prediction,
    true_answer,
    view_predictions,
    multiview=True,
):
    view_records = {}
    for method, prediction in view_predictions.items():
        view_records[method] = {
            "task_id": task_id,
            "predicted_answer": prediction,
            "generated_graph": {"roles": ["Math Solver"]},
            "agent_outputs": [
                {"node": 0, "role": "Math Solver", "outputs": [f"The answer is {prediction}"]},
                {"node": 1, "role": "Math Solver", "outputs": [f"The answer is {prediction}"]},
            ],
        }
    return {
        "task_id": task_id,
        "question": "q",
        "true_answer": true_answer,
        "baseline_prediction": baseline_prediction,
        "baseline_is_solved": baseline_prediction == true_answer,
        "predicted_answer": baseline_prediction,
        "is_solved": baseline_prediction == true_answer,
        "multiview_was_run": multiview,
        "view_predictions": view_predictions,
        "view_records": view_records,
    }


class CascadeMultiviewReplayTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/cascade_multiview_replay.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_early_accepts_valid_baseline_after_two_supporting_views(self):
        from experiment.aqua.cascade_multiview_replay import build_cascade_record

        record = build_cascade_record(
            _record(
                "task_keep",
                baseline_prediction="C",
                true_answer="C",
                view_predictions={
                    "router": "C",
                    "conservative": "C",
                    "calibrated": "A",
                    "candidate": "B",
                },
            )
        )

        self.assertEqual(record["predicted_answer"], "C")
        self.assertEqual(record["selected_source"], "baseline_early_accept")
        self.assertEqual(record["view_calls"], 2)
        self.assertNotIn("true_answer", record["decision_features"])
        self.assertNotIn("is_solved", record["decision_features"])

    def test_switches_only_with_objective_and_support_threshold(self):
        from experiment.aqua.cascade_multiview_replay import build_cascade_record

        record = build_cascade_record(
            _record(
                "task_fix",
                baseline_prediction=None,
                true_answer="A",
                view_predictions={
                    "router": "A",
                    "conservative": "A",
                    "calibrated": "A",
                    "candidate": "B",
                },
            )
        )

        self.assertEqual(record["predicted_answer"], "A")
        self.assertEqual(record["selected_source"], "cascade_objective")
        self.assertEqual(record["view_calls"], 3)
        self.assertTrue(record["is_solved"])

    def test_keeps_baseline_when_invalid_case_lacks_three_view_support(self):
        from experiment.aqua.cascade_multiview_replay import build_cascade_record

        record = build_cascade_record(
            _record(
                "task_block",
                baseline_prediction=None,
                true_answer="C",
                view_predictions={
                    "router": "B",
                    "conservative": "B",
                    "calibrated": "C",
                    "candidate": "A",
                },
            )
        )

        self.assertIsNone(record["predicted_answer"])
        self.assertEqual(record["selected_source"], "baseline")
        self.assertEqual(record["view_calls"], 4)

    def test_real_r069_cascade_preserves_accuracy_with_fewer_view_calls(self):
        from experiment.aqua.cascade_multiview_replay import build_r071_payload

        payload = build_r071_payload("experiment/aqua")
        summary = payload["summary"]

        self.assertEqual(summary["overall"], "29/34")
        self.assertEqual(summary["baseline"], "26/34")
        self.assertEqual(summary["fix_harm"], "3/0")
        self.assertEqual(summary["clean"], "27/28")
        self.assertEqual(summary["clean_fix_harm"], "3/0")
        self.assertEqual(summary["cascade_view_calls"], 56)
        self.assertEqual(summary["full_view_calls"], 100)
        self.assertEqual(summary["switch_tasks"], ["task_56", "task_8", "task_188"])
        self.assertLess(
            payload["cost_estimate"]["estimated_cost"],
            payload["cost_estimate"]["r069_full_integrated_cost"],
        )
        self.assertEqual(payload["claim_boundary"], "cascade_replay_over_r069_fresh_traces_not_new_api_run")


if __name__ == "__main__":
    unittest.main()
