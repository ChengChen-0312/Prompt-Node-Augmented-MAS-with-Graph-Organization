import unittest

from experiment.mmlu.r252_mmlu_transfer_preflight import (
    build_source_lookup,
    build_variant_manifest_rows,
    scan_manifest_prompt_leakage,
    summarize_preflight_records,
)


class TestR252MMLUTransferPreflight(unittest.TestCase):
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

    def test_variant_manifest_rows_include_controls_and_api_variants(self):
        rows = build_variant_manifest_rows([self._probe_row()], build_source_lookup([self._source_row()]))
        variants = {row["control_variant"] for row in rows}

        self.assertEqual(
            variants,
            {
                "arg_baseline_fixed",
                "abstain_keep_arg",
                "plain_requery",
                "node_only_no_promptedge_text",
                "proposed_promptnode_promptedge",
            },
        )

    def test_model_visible_input_excludes_evaluation_labels(self):
        rows = build_variant_manifest_rows([self._probe_row()], build_source_lookup([self._source_row()]))
        proposed = [row for row in rows if row["control_variant"] == "proposed_promptnode_promptedge"][0]

        self.assertIn("true_answer", proposed["evaluation_only"])
        self.assertNotIn("true_answer", proposed["model_visible_input"])
        self.assertNotIn("arg_error", proposed["model_visible_input"])

    def test_prompt_leakage_scan_blocks_task_id_and_label_fields(self):
        rows = build_variant_manifest_rows([self._probe_row()], build_source_lookup([self._source_row()]))
        proposed = [row for row in rows if row["control_variant"] == "proposed_promptnode_promptedge"][0]

        clean = scan_manifest_prompt_leakage(proposed)
        self.assertEqual(clean["leakage_violations"], 0)

        bad = dict(proposed)
        bad["model_visible_messages"] = [{"role": "user", "content": "task_id: mmlu-1 true_answer: C"}]
        blocked = scan_manifest_prompt_leakage(bad)
        self.assertGreater(blocked["leakage_violations"], 0)

    def test_summary_requires_balanced_variants_and_cost_cap(self):
        rows = build_variant_manifest_rows([self._probe_row()], build_source_lookup([self._source_row()]))
        summary = summarize_preflight_records(rows, cost_cap=0.45)

        self.assertTrue(summary["variant_balance_pass"])
        self.assertTrue(summary["estimated_cost_within_cap"])


if __name__ == "__main__":
    unittest.main()
