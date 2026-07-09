import unittest

from experiment.mmlu.r256_transfer_failure_mechanism import (
    classify_task_delta,
    summarize_failure_modes,
)


class TestR256TransferFailureMechanism(unittest.TestCase):
    def _row(self, variant, correct, fix=False, harm=False):
        return {
            "control_variant": variant,
            "is_correct": correct,
            "fix": fix,
            "harm": harm,
            "predicted_answer": "A",
            "true_answer": "B",
        }

    def test_classifies_promptedge_regression_when_node_fixes_but_proposed_misses(self):
        task = {
            "plain_requery": self._row("plain_requery", True, fix=True),
            "node_only_no_promptedge_text": self._row("node_only_no_promptedge_text", True, fix=True),
            "proposed_promptnode_promptedge": self._row("proposed_promptnode_promptedge", False),
        }

        tags = classify_task_delta(task)

        self.assertIn("node_fix_lost_by_promptedge", tags)

    def test_classifies_proposed_harm(self):
        task = {
            "plain_requery": self._row("plain_requery", True),
            "node_only_no_promptedge_text": self._row("node_only_no_promptedge_text", False, harm=True),
            "proposed_promptnode_promptedge": self._row("proposed_promptnode_promptedge", False, harm=True),
        }

        tags = classify_task_delta(task)

        self.assertIn("proposed_control_harm", tags)

    def test_summary_counts_modes(self):
        tasks = {
            "t1": {
                "plain_requery": self._row("plain_requery", True, fix=True),
                "node_only_no_promptedge_text": self._row("node_only_no_promptedge_text", True, fix=True),
                "proposed_promptnode_promptedge": self._row("proposed_promptnode_promptedge", False),
            }
        }

        summary = summarize_failure_modes(tasks)

        self.assertEqual(summary["mode_counts"]["node_fix_lost_by_promptedge"], 1)


if __name__ == "__main__":
    unittest.main()
