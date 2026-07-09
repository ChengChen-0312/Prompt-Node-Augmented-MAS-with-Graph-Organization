import subprocess
import sys
import unittest


class SurgicalCascadeTriggerReplayTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/surgical_cascade_trigger_replay.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_trigger_runs_for_invalid_baseline_without_outcome_fields(self):
        from experiment.aqua.surgical_cascade_trigger_replay import should_run_surgical_trigger

        features = {
            "invalid_baseline_prediction": True,
            "weak_final_support": False,
            "low_direct_coverage": False,
            "non_promptnode_output_count": 3,
            "direct_conflict": False,
            "true_answer": "A",
            "is_solved": False,
            "task_id": "task_56",
        }

        self.assertTrue(should_run_surgical_trigger(features))

    def test_trigger_runs_for_weak_low_coverage_two_agent_case(self):
        from experiment.aqua.surgical_cascade_trigger_replay import should_run_surgical_trigger

        features = {
            "invalid_baseline_prediction": False,
            "weak_final_support": True,
            "low_direct_coverage": True,
            "non_promptnode_output_count": 2,
            "direct_conflict": False,
        }

        self.assertTrue(should_run_surgical_trigger(features))

    def test_trigger_skips_direct_conflict_and_three_agent_missing_vote_cases(self):
        from experiment.aqua.surgical_cascade_trigger_replay import should_run_surgical_trigger

        conflict_features = {
            "invalid_baseline_prediction": False,
            "weak_final_support": True,
            "low_direct_coverage": False,
            "non_promptnode_output_count": 2,
            "direct_conflict": True,
        }
        three_agent_missing_vote_features = {
            "invalid_baseline_prediction": False,
            "weak_final_support": False,
            "low_direct_coverage": False,
            "non_promptnode_output_count": 3,
            "direct_conflict": False,
            "missing_direct_vote": True,
        }

        self.assertFalse(should_run_surgical_trigger(conflict_features))
        self.assertFalse(should_run_surgical_trigger(three_agent_missing_vote_features))

    def test_real_r072_surgical_replay_preserves_accuracy_with_fewer_view_calls(self):
        from experiment.aqua.surgical_cascade_trigger_replay import (
            build_surgical_records,
            load_jsonl,
            summarize_surgical_records,
        )

        records = build_surgical_records(
            load_jsonl("experiment/aqua/aqua_tail34_r072_integrated_cascade_results.jsonl")
        )
        summary = summarize_surgical_records(records)

        self.assertEqual(summary["overall"], "29/34")
        self.assertEqual(summary["baseline"], "27/34")
        self.assertEqual(summary["multiview_run"], "10/34")
        self.assertEqual(summary["view_calls"], "21/40")
        self.assertEqual(summary["fix_harm"], "2/0")
        self.assertEqual(summary["fix_tasks"], ["task_56", "task_188"])
        self.assertEqual(summary["harm_tasks"], [])
        self.assertNotIn("task_114", summary["run_tasks"])
        self.assertNotIn("task_250", summary["run_tasks"])

    def test_cost_estimate_uses_measured_r072_view_overhead(self):
        from experiment.aqua.surgical_cascade_trigger_replay import estimate_surgical_cost

        cost = estimate_surgical_cost(
            baseline_cost=0.932850,
            reference_total_cost=2.826040,
            reference_view_calls=58,
            surgical_view_calls=21,
        )

        self.assertEqual(cost["estimated_cost"], 1.618315)
        self.assertEqual(cost["saving_vs_r072"], 1.207725)
        self.assertEqual(cost["relative_cost_vs_arg"], 1.73)


if __name__ == "__main__":
    unittest.main()
