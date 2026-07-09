import unittest

from experiment.mmlu.r259_promptnode_v2_api_executor import (
    apply_v2_response,
    parse_v2_response,
    summarize_v2_records,
)


class TestR259PromptNodeV2ApiExecutor(unittest.TestCase):
    def _record(self):
        return {
            "task_id": "mmlu-1",
            "control_variant": "proposed_v2_independent_guarded_pnpe",
            "selection_role": "arg_error",
            "api_required": True,
            "evaluation_only": {
                "true_answer": "C",
                "arg_prediction": "A",
                "arg_error": True,
            },
        }

    def test_parse_switch_final_label(self):
        parsed = parse_v2_response('{"action":"SWITCH","final_label":"C","independent_label":"C"}')

        self.assertEqual(parsed["action"], "SWITCH")
        self.assertEqual(parsed["final_label"], "C")

    def test_keep_arg_forces_arg_prediction(self):
        row = apply_v2_response(self._record(), '{"action":"KEEP_ARG","final_label":"C"}', True)

        self.assertEqual(row["predicted_answer"], "A")
        self.assertFalse(row["fix"])

    def test_switch_scores_fix(self):
        row = apply_v2_response(self._record(), '{"action":"SWITCH","final_label":"C"}', True)

        self.assertEqual(row["predicted_answer"], "C")
        self.assertTrue(row["fix"])

    def test_summary_counts_api(self):
        rows = [
            apply_v2_response(self._record(), '{"action":"SWITCH","final_label":"C"}', True),
        ]

        summary = summarize_v2_records(rows, api_cost=0.01, prompt_tokens=5, completion_tokens=2)

        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["fixes"], 1)
        self.assertEqual(summary["api_executed"], 1)


if __name__ == "__main__":
    unittest.main()
