import unittest

from experiment.mmlu.r233_tiny_api_diagnostic_executor import (
    apply_router_response,
    parse_router_response,
    summarize_executed_records,
)


class TestR233TinyApiDiagnosticExecutor(unittest.TestCase):
    def _record(self, api_required=True):
        return {
            "task_id": "task_1",
            "control_variant": "proposed_router_final" if api_required else "abstain_only_router",
            "api_required": api_required,
            "model": "gpt-4o-2024-08-06",
            "true_answer": "D",
            "baseline_prediction": "B",
            "objective_prediction": "D",
            "planned_action": "model_router" if api_required else "abstain",
            "planned_selected_label": "NONE" if api_required else "B",
            "max_completion_tokens": 24,
            "model_visible_messages": [{"role": "user", "content": "Question"}] if api_required else [],
        }

    def test_parse_json_router_response(self):
        parsed = parse_router_response('{"action":"switch_to_objective","selected_label":"D","rationale":"ok"}')

        self.assertEqual(parsed["action"], "switch_to_objective")
        self.assertEqual(parsed["selected_label"], "D")

    def test_parse_code_fenced_router_response(self):
        parsed = parse_router_response('```json\n{"action":"abstain","selected_label":"NONE"}\n```')

        self.assertEqual(parsed["action"], "abstain")
        self.assertEqual(parsed["selected_label"], "NONE")

    def test_apply_api_router_response_scores_fix(self):
        record = apply_router_response(
            self._record(api_required=True),
            '{"action":"switch_to_objective","selected_label":"D","rationale":"objective is stronger"}',
            api_executed=True,
        )

        self.assertEqual(record["predicted_answer"], "D")
        self.assertTrue(record["is_correct"])
        self.assertTrue(record["fix"])
        self.assertFalse(record["harm"])

    def test_apply_abstain_response_keeps_baseline(self):
        record = apply_router_response(
            self._record(api_required=True),
            '{"action":"abstain","selected_label":"NONE"}',
            api_executed=True,
        )

        self.assertEqual(record["predicted_answer"], "B")
        self.assertFalse(record["is_correct"])

    def test_deterministic_record_uses_planned_label(self):
        record = apply_router_response(self._record(api_required=False), "", api_executed=False)

        self.assertEqual(record["predicted_answer"], "B")
        self.assertFalse(record["api_executed"])

    def test_summary_counts_accuracy_and_fix_harm(self):
        records = [
            apply_router_response(
                self._record(api_required=True),
                '{"action":"switch_to_objective","selected_label":"D"}',
                api_executed=True,
            ),
            apply_router_response(self._record(api_required=False), "", api_executed=False),
        ]

        summary = summarize_executed_records(records, api_cost=0.01, prompt_tokens=10, completion_tokens=5)

        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["correct"], 1)
        self.assertEqual(summary["fixes"], 1)
        self.assertEqual(summary["harms"], 0)
        self.assertEqual(summary["api_executed"], 1)


if __name__ == "__main__":
    unittest.main()
