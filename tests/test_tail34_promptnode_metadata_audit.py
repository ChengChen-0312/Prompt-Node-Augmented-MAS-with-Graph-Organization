import subprocess
import sys
import unittest


class Tail34PromptNodeMetadataAuditTests(unittest.TestCase):
    def test_real_tail34_sources_separate_positive_signal_from_promptnode_metadata(self):
        from experiment.aqua.tail34_promptnode_metadata_audit import build_metadata_audit

        rows, summary = build_metadata_audit()
        by_run = {row["run_id"]: row for row in rows}

        self.assertEqual(summary["sources"], len(rows))
        self.assertEqual(by_run["R058_dense_generated_pn"]["records_with_promptnode_roles"], 34)
        self.assertEqual(by_run["R058_dense_generated_pn"]["records"], 34)
        self.assertEqual(by_run["R064_router_view"]["records_with_promptnode_roles"], 0)
        self.assertEqual(by_run["R072_fresh_cascade"]["records_with_promptnode_roles"], 0)
        self.assertEqual(by_run["R074_fresh_surgical_cascade"]["records_with_promptnode_roles"], 0)
        self.assertEqual(summary["positive_accuracy_sources_with_promptnode_roles"], 0)
        self.assertIn("positive tail34 sources lack explicit PromptNode graph metadata", summary["claim_boundary"])

    def test_cli_file_execution_can_import_project_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "experiment/aqua/tail34_promptnode_metadata_audit.py",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
