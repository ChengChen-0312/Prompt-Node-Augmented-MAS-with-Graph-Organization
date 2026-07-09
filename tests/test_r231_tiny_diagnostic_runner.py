import unittest

from experiment.mmlu.r231_tiny_diagnostic_runner import (
    build_diagnostic_record,
    build_model_visible_messages,
    build_source_lookup,
    estimate_request_cost,
    scan_message_leakage,
    summarize_diagnostic_records,
)


class TestR231TinyDiagnosticRunner(unittest.TestCase):
    def _manifest_row(self, variant="proposed_router_final", action="switch_to_objective"):
        return {
            "task_id": "task_1",
            "control_variant": variant,
            "router_action": action,
            "target_option_label": "D" if action == "switch_to_objective" else "NONE",
            "model_visible_input": {
                "baseline_prediction": "B",
                "objective_prediction": "D",
                "objective_prediction_differs_from_baseline": True,
                "objective_top_score": 3,
                "baseline_direct_majority": "B",
                "baseline_direct_majority_count": 1,
                "baseline_direct_valid_vote_count": 1,
                "baseline_direct_votes_split": False,
            },
            "router_final_schema": {
                "allowed_option_labels": ["A", "B", "C", "D", "E", "NONE"],
                "forbidden_model_visible_fields": [
                    "task_id",
                    "true_answer",
                    "gold_answer",
                    "is_correct",
                    "correctness",
                    "audit_label",
                    "target_option_label",
                ],
                "gold_answer_used": False,
                "promptedge_text_policy": {"edge_text_as_prompt": True},
            },
        }

    def _source_row(self):
        return {
            "task_id": "task_1",
            "question": "What is 2 + 2? Choices: A)1 B)2 C)3 D)4 E)5",
            "true_answer": "D",
            "baseline_prediction": "B",
        }

    def test_source_lookup_keeps_question_for_join(self):
        lookup = build_source_lookup([self._source_row()])

        self.assertIn("task_1", lookup)
        self.assertEqual(lookup["task_1"]["question"], self._source_row()["question"])

    def test_prompt_messages_exclude_forbidden_machine_fields(self):
        messages = build_model_visible_messages(self._manifest_row(), self._source_row())
        combined = "\n".join(message["content"] for message in messages)

        self.assertIn("What is 2 + 2?", combined)
        self.assertIn("PromptEdge", combined)
        self.assertNotIn("task_id", combined)
        self.assertNotIn("true_answer", combined)
        self.assertNotIn("target_option_label", combined)
        self.assertEqual(scan_message_leakage(messages, self._manifest_row())["leakage_violations"], 0)

    def test_node_only_control_disables_promptedge_text(self):
        row = self._manifest_row(variant="node_only_no_promptedge_text")
        row["router_final_schema"]["promptedge_text_policy"] = {"edge_text_as_prompt": False}

        messages = build_model_visible_messages(row, self._source_row())
        combined = "\n".join(message["content"] for message in messages)

        self.assertIn("edge_text_enabled=false", combined)
        self.assertNotIn("edge_text_enabled=true", combined)

    def test_deterministic_abstain_control_keeps_baseline_without_api(self):
        record = build_diagnostic_record(
            self._manifest_row(variant="abstain_only_router", action="abstain"),
            {"task_1": self._source_row()},
            model="gpt-4o-2024-08-06",
            max_completion_tokens=24,
        )

        self.assertFalse(record["api_required"])
        self.assertEqual(record["planned_selected_label"], "B")
        self.assertEqual(record["planned_action"], "abstain")

    def test_proposed_record_requires_api_and_has_cost_estimate(self):
        record = build_diagnostic_record(
            self._manifest_row(),
            {"task_1": self._source_row()},
            model="gpt-4o-2024-08-06",
            max_completion_tokens=24,
        )

        self.assertTrue(record["api_required"])
        self.assertGreater(record["estimated_cost"], 0.0)
        self.assertEqual(record["prompt_leakage_violations"], 0)

    def test_summary_counts_api_calls_and_cost_cap(self):
        source_lookup = {"task_1": self._source_row()}
        records = [
            build_diagnostic_record(self._manifest_row(), source_lookup, "gpt-4o-2024-08-06", 24),
            build_diagnostic_record(
                self._manifest_row(variant="abstain_only_router", action="abstain"),
                source_lookup,
                "gpt-4o-2024-08-06",
                24,
            ),
        ]

        summary = summarize_diagnostic_records(records, cost_cap=0.45)

        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["api_required"], 1)
        self.assertTrue(summary["estimated_cost_within_cap"])

    def test_cost_estimate_is_positive_for_nonempty_messages(self):
        estimate = estimate_request_cost(
            [{"role": "user", "content": "Choose A, B, C, D, E, or NONE."}],
            model="gpt-4o-2024-08-06",
            max_completion_tokens=8,
        )

        self.assertGreater(estimate["estimated_cost"], 0.0)
        self.assertGreater(estimate["prompt_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
