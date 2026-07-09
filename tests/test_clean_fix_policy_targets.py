import subprocess
import sys
import unittest


class CleanFixPolicyTargetsTests(unittest.TestCase):
    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/clean_fix_policy_targets.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_real_targets_mark_clean_fixes_and_noisy_boundary(self):
        from experiment.aqua.clean_fix_policy_targets import build_clean_fix_policy_targets

        targets, summary = build_clean_fix_policy_targets()
        by_task = {target["task_id"]: target for target in targets}

        self.assertEqual(summary["clean_positive_tasks"], ["task_188", "task_56", "task_8"])
        self.assertEqual(summary["noisy_optional_tasks"], ["task_108"])
        self.assertEqual(by_task["task_108"]["target_class"], "noisy_optional")
        self.assertEqual(by_task["task_188"]["target_class"], "clean_fix_preserve")
        self.assertEqual(
            by_task["task_188"]["recommended_policy"],
            "run_on_direct_conflict_with_alternative_vote",
        )

    def test_policy_inputs_exclude_outcome_fields(self):
        from experiment.aqua.clean_fix_policy_targets import build_clean_fix_policy_targets

        targets, summary = build_clean_fix_policy_targets()
        forbidden = set(summary["forbidden_policy_input_fields"])

        for target in targets:
            self.assertFalse(forbidden.intersection(target["policy_input"]))
            self.assertNotIn("true_answer", target["policy_input"])
            self.assertNotIn("is_solved", target["policy_input"])
            self.assertNotIn("baseline_is_solved", target["policy_input"])


if __name__ == "__main__":
    unittest.main()
