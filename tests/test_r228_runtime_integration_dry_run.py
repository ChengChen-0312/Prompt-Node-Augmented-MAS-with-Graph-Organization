import unittest

from experiment.mmlu.r228_runtime_integration_dry_run import (
    build_integration_record,
    summarize_integration_records,
)


class TestR228RuntimeIntegrationDryRun(unittest.TestCase):
    def _row(self, action="switch_to_objective", label="C", variant="proposed_router_final"):
        return {
            "task_id": "task_1",
            "control_variant": variant,
            "router_action": action,
            "target_option_label": label,
            "model_visible_input": {"baseline_prediction": "A", "objective_prediction": label},
            "router_final_schema": {
                "allowed_option_labels": ["A", "B", "C", "D", "E", "NONE"],
                "gold_answer_used": False,
            },
        }

    def test_switch_record_selects_router_label(self):
        record = build_integration_record(self._row("switch_to_objective", "C"))

        self.assertTrue(record["would_switch"])
        self.assertEqual(record["baseline_answer"], "A")
        self.assertEqual(record["router_final_answer"], "C")
        self.assertEqual(record["fallback_reason"], "router_switch")

    def test_abstain_record_keeps_baseline(self):
        record = build_integration_record(self._row("abstain", "NONE"))

        self.assertFalse(record["would_switch"])
        self.assertEqual(record["router_final_answer"], "A")
        self.assertEqual(record["fallback_reason"], "router_abstain")

    def test_cost_matched_arg_requery_does_not_apply_router(self):
        row = self._row("switch_to_objective", "C", "cost_matched_arg_requery")

        record = build_integration_record(row)

        self.assertFalse(record["would_switch"])
        self.assertEqual(record["router_final_answer"], "A")
        self.assertEqual(record["fallback_reason"], "cost_matched_arg_requery")

    def test_summary_counts_switches_and_missing_fields(self):
        records = [
            build_integration_record(self._row("switch_to_objective", "C")),
            build_integration_record(self._row("abstain", "NONE")),
        ]

        summary = summarize_integration_records(records)

        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["would_switch"], 1)
        self.assertEqual(summary["missing_required_fields"], 0)


if __name__ == "__main__":
    unittest.main()
