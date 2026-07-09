import unittest


def _baseline_record(task_id="task_x", prediction="A", true_answer="B", votes=None):
    votes = votes if votes is not None else ["A"]
    return {
        "task_id": task_id,
        "question": "q",
        "true_answer": true_answer,
        "predicted_answer": prediction,
        "agent_outputs": [
            {"node": index, "role": "Math Solver", "outputs": [f"The answer is {vote}"]}
            for index, vote in enumerate(votes)
        ]
        + [{"node": 9, "role": "Programming Expert", "outputs": ["answer = 42"]}],
    }


def _selector_record(task_id="task_x", prediction="B", true_answer="B", baseline_prediction="A"):
    return {
        "task_id": task_id,
        "question": "q",
        "true_answer": true_answer,
        "predicted_answer": prediction,
        "selected_source": "objective_top" if prediction != baseline_prediction else "baseline",
        "baseline_prediction": baseline_prediction,
    }


class SelectiveMultiviewTriggerTests(unittest.TestCase):
    def test_trigger_runs_on_missing_direct_vote_without_outcome_fields(self):
        from experiment.aqua.selective_multiview_trigger import (
            extract_multiview_trigger_features,
            should_run_multiview,
        )

        features = extract_multiview_trigger_features(
            _baseline_record(prediction="A", true_answer="B", votes=["A", "A"])
        )

        self.assertTrue(features["missing_direct_vote"])
        self.assertTrue(should_run_multiview(features))
        self.assertNotIn("true_answer", features)
        self.assertNotIn("is_solved", features)
        self.assertNotIn("task_id", features)

    def test_build_records_uses_objective_only_when_triggered(self):
        from experiment.aqua.selective_multiview_trigger import build_selective_multiview_records

        baseline_records = {
            "task_run": _baseline_record("task_run", prediction="A", true_answer="B", votes=["A"]),
            "task_skip": {
                **_baseline_record("task_skip", prediction="C", true_answer="C", votes=["C", "C"]),
                "agent_outputs": [
                    {"node": 0, "role": "Math Solver", "outputs": ["The answer is C"]},
                    {"node": 1, "role": "Inspector", "outputs": ["The answer is C"]},
                ],
            },
        }
        selector_records = {
            "task_run": _selector_record("task_run", prediction="B", true_answer="B", baseline_prediction="A"),
            "task_skip": _selector_record("task_skip", prediction="A", true_answer="C", baseline_prediction="C"),
        }

        records = build_selective_multiview_records(baseline_records, selector_records)
        by_task = {record["task_id"]: record for record in records}

        self.assertEqual(by_task["task_run"]["predicted_answer"], "B")
        self.assertEqual(by_task["task_run"]["selected_source"], "objective_top")
        self.assertTrue(by_task["task_run"]["multiview_would_run"])
        self.assertEqual(by_task["task_skip"]["predicted_answer"], "C")
        self.assertEqual(by_task["task_skip"]["selected_source"], "baseline")
        self.assertFalse(by_task["task_skip"]["multiview_would_run"])

    def test_cost_estimate_scales_view_cost_by_run_fraction(self):
        from experiment.aqua.selective_multiview_trigger import estimate_selective_cost

        cost = estimate_selective_cost(
            baseline_summary={"cost": 1.0, "prompt_tokens": 10, "completion_tokens": 5, "total_tasks": 10},
            view_summaries=[
                {"cost": 2.0, "prompt_tokens": 20, "completion_tokens": 10, "total_tasks": 10},
                {"cost": 3.0, "prompt_tokens": 30, "completion_tokens": 15, "total_tasks": 10},
            ],
            run_count=4,
            total_tasks=10,
        )

        self.assertAlmostEqual(cost["estimated_cost"], 3.0)
        self.assertAlmostEqual(cost["full_multiview_cost"], 6.0)
        self.assertAlmostEqual(cost["relative_cost_vs_arg"], 3.0)
        self.assertAlmostEqual(cost["cost_saving_vs_full_multiview"], 3.0)

    def test_real_tail34_selective_trigger_preserves_objective_accuracy_with_lower_cost(self):
        from experiment.aqua.selective_multiview_trigger import build_tail34_selective_payload

        payload = build_tail34_selective_payload("experiment/aqua")
        summary = payload["summary"]

        self.assertEqual(summary["overall"], "31/34")
        self.assertEqual(summary["baseline"], "28/34")
        self.assertEqual(summary["fix_harm"], "3/0")
        self.assertEqual(summary["clean"], "28/28")
        self.assertEqual(summary["clean_fix_harm"], "1/0")
        self.assertEqual(summary["multiview_run_count"], 22)
        self.assertEqual(summary["switch_tasks"], ["task_114", "task_59", "task_108", "task_250"])
        self.assertLess(payload["cost_estimate"]["estimated_cost"], payload["cost_estimate"]["full_multiview_cost"])
        self.assertEqual(payload["claim_boundary"], "selective_multiview_replay_not_fresh_api_run")


if __name__ == "__main__":
    unittest.main()
