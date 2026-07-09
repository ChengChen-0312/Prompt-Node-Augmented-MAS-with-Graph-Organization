import unittest

from experiment.mmlu.r254_mmlu_transfer_result_analysis import (
    assess_transfer_claims,
    summarize_by_variant_and_role,
)


class TestR254MMLUTransferResultAnalysis(unittest.TestCase):
    def _row(self, variant, correct, fix=False, harm=False, role="arg_error"):
        return {
            "task_id": f"{variant}-{role}",
            "control_variant": variant,
            "selection_role": role,
            "is_correct": correct,
            "fix": fix,
            "harm": harm,
            "api_cost": 0.0,
        }

    def test_summarize_by_variant_and_role_counts_fix_harm(self):
        rows = [
            self._row("arg_baseline_fixed", False),
            self._row("proposed_promptnode_promptedge", True, fix=True),
        ]

        summary = summarize_by_variant_and_role(rows)

        self.assertEqual(summary["by_variant"]["proposed_promptnode_promptedge"]["correct"], 1)
        self.assertEqual(summary["by_variant"]["proposed_promptnode_promptedge"]["fixes"], 1)

    def test_assessment_rejects_transfer_if_proposed_loses_to_plain(self):
        rows = [
            self._row("arg_baseline_fixed", False),
            self._row("plain_requery", True, fix=True),
            self._row("node_only_no_promptedge_text", True, fix=True),
            self._row("proposed_promptnode_promptedge", False),
        ]

        assessment = assess_transfer_claims(rows)

        self.assertFalse(assessment["transfer_superiority_supported"])
        self.assertFalse(assessment["proposed_beats_plain_requery"])


if __name__ == "__main__":
    unittest.main()
