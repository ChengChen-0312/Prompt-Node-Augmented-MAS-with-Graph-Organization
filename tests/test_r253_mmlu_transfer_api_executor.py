import unittest

from experiment.mmlu.r253_mmlu_transfer_api_executor import (
    apply_answer_response,
    parse_answer_response,
    summarize_executed_records,
)


class TestR253MMLUTransferApiExecutor(unittest.TestCase):
    def _record(self, api_required=True):
        return {
            "task_id": "mmlu-1",
            "control_variant": "proposed_promptnode_promptedge" if api_required else "arg_baseline_fixed",
            "selection_role": "arg_error",
            "api_required": api_required,
            "model": "gpt-4o-2024-08-06",
            "evaluation_only": {
                "true_answer": "C",
                "arg_prediction": "A",
                "arg_error": True,
            },
            "deterministic_selected_label": "A",
            "model_visible_messages": [{"role": "user", "content": "Question"}] if api_required else [],
        }

    def test_parse_json_answer_response(self):
        parsed = parse_answer_response('{"selected_label":"C","rationale":"checked"}')

        self.assertEqual(parsed["selected_label"], "C")
        self.assertTrue(parsed["parse_ok"])

    def test_parse_text_answer_response(self):
        parsed = parse_answer_response("Answer: D")

        self.assertEqual(parsed["selected_label"], "D")

    def test_apply_api_response_scores_fix(self):
        row = apply_answer_response(self._record(), '{"selected_label":"C"}', api_executed=True)

        self.assertEqual(row["predicted_answer"], "C")
        self.assertTrue(row["is_correct"])
        self.assertTrue(row["fix"])
        self.assertFalse(row["harm"])

    def test_deterministic_record_uses_arg_prediction(self):
        row = apply_answer_response(self._record(api_required=False), "", api_executed=False)

        self.assertEqual(row["predicted_answer"], "A")
        self.assertFalse(row["api_executed"])

    def test_summary_groups_by_variant(self):
        rows = [
            apply_answer_response(self._record(), '{"selected_label":"C"}', api_executed=True),
            apply_answer_response(self._record(api_required=False), "", api_executed=False),
        ]

        summary = summarize_executed_records(rows, api_cost=0.01, prompt_tokens=10, completion_tokens=4)

        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["fixes"], 1)
        self.assertEqual(summary["api_executed"], 1)
        self.assertIn("proposed_promptnode_promptedge", summary["by_variant"])


if __name__ == "__main__":
    unittest.main()
