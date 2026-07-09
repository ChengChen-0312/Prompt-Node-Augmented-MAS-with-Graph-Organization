import subprocess
import sys
import unittest


class FreshCascadeParetoReportTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/fresh_cascade_pareto_report.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_real_fresh_runs_are_ranked_by_cost_and_clean_fix_boundary(self):
        from experiment.aqua.fresh_cascade_pareto_report import build_fresh_pareto_payload

        payload = build_fresh_pareto_payload()
        by_run = {row["run_id"]: row for row in payload["rows"]}

        self.assertEqual(by_run["R069"]["overall"], "29/34")
        self.assertEqual(by_run["R072"]["overall"], "29/34")
        self.assertEqual(by_run["R074"]["overall"], "29/34")
        self.assertLess(by_run["R074"]["cost"], by_run["R072"]["cost"])
        self.assertLess(by_run["R072"]["cost"], by_run["R069"]["cost"])
        self.assertEqual(by_run["R074"]["clean_fix_harm"], "0/0")
        self.assertEqual(by_run["R072"]["clean_fix_harm"], "2/0")
        self.assertEqual(payload["accuracy_cost_frontier"], ["R074"])
        self.assertEqual(payload["recommended_next"], "distill_clean_fix_preserving_trigger_or_graph_policy")

    def test_stability_sets_identify_clean_fix_loss_after_surgical_compression(self):
        from experiment.aqua.fresh_cascade_pareto_report import build_fresh_pareto_payload

        stability = build_fresh_pareto_payload()["stability"]

        self.assertEqual(stability["r072_clean_fixes_lost_by_r074"], ["task_188", "task_56"])
        self.assertEqual(stability["r074_new_fix_not_in_r072"], ["task_108"])
        self.assertEqual(stability["common_harms"], [])


if __name__ == "__main__":
    unittest.main()
