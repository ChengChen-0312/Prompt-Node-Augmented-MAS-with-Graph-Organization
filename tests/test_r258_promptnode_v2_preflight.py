import unittest

from experiment.mmlu.r258_promptnode_v2_preflight import (
    build_v2_manifest_rows,
    scan_v2_prompt_leakage,
    summarize_v2_preflight,
)
from experiment.mmlu.r252_mmlu_transfer_preflight import build_source_lookup


class TestR258PromptNodeV2Preflight(unittest.TestCase):
    def _probe_row(self):
        return {
            "task_id": "mmlu-1",
            "features": {"subject": "math"},
            "labels": {"predicted_answer": "A", "true_answer": "C", "arg_error": True},
            "selection_role": "arg_error",
        }

    def _source_row(self):
        return {
            "task_id": "mmlu-1",
            "subject": "math",
            "question": "Q?\nOption A: 1\nOption B: 2\nOption C: 3\nOption D: 4",
            "predicted_answer": "A",
            "true_answer": "C",
            "is_correct": False,
        }

    def test_v2_manifest_has_arg_reference_and_api_variant(self):
        rows = build_v2_manifest_rows([self._probe_row()], build_source_lookup([self._source_row()]))
        variants = {row["control_variant"] for row in rows}

        self.assertEqual(variants, {"arg_baseline_fixed", "proposed_v2_independent_guarded_pnpe"})

    def test_v2_prompt_has_guard_contract_without_label_leakage(self):
        rows = build_v2_manifest_rows([self._probe_row()], build_source_lookup([self._source_row()]))
        v2 = [row for row in rows if row["api_required"]][0]
        prompt = "\n".join(message["content"] for message in v2["model_visible_messages"])

        self.assertIn("KEEP_ARG", prompt)
        self.assertIn("two evidence checks", prompt)
        self.assertNotIn("true_answer", prompt)
        self.assertEqual(scan_v2_prompt_leakage(v2)["leakage_violations"], 0)

    def test_v2_summary_passes_for_balanced_low_cost_rows(self):
        rows = build_v2_manifest_rows([self._probe_row()], build_source_lookup([self._source_row()]))
        summary = summarize_v2_preflight(rows, cost_cap=0.45)

        self.assertTrue(summary["preflight_pass"])


if __name__ == "__main__":
    unittest.main()
