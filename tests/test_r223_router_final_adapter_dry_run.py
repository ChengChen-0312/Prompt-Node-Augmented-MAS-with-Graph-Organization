import unittest

from experiment.mmlu.r223_router_final_adapter_dry_run import (
    adapt_router_record,
    summarize_adapter_outputs,
)


class TestR223RouterFinalAdapterDryRun(unittest.TestCase):
    def _row(self, action="switch_to_objective", label="C", variant="proposed"):
        return {
            "control_variant": variant,
            "split_role": "train",
            "router_action": action,
            "target_option_label": label if action == "switch_to_objective" else "NONE",
            "model_visible_input": {"objective_prediction": label},
            "router_final_schema": {
                "promptedge_text_policy": {"edge_text_as_prompt": True},
                "forbidden_model_visible_fields": ["task_id", "is_correct", "true_answer"],
                "gold_answer_used": False,
            },
        }

    def test_adapter_switches_to_target_label_for_non_abstain_record(self):
        output = adapt_router_record(self._row("switch_to_objective", "D"))

        self.assertTrue(output["would_switch"])
        self.assertEqual(output["selected_label"], "D")
        self.assertTrue(output["uses_promptedge_text"])
        self.assertTrue(output["leakage_pass"])

    def test_adapter_abstains_on_none_label(self):
        output = adapt_router_record(self._row("abstain", "C"))

        self.assertFalse(output["would_switch"])
        self.assertEqual(output["selected_label"], "NONE")

    def test_adapter_reflects_no_edge_text_control(self):
        row = self._row("switch_to_objective", "C", "node_only_no_promptedge_text")
        row["router_final_schema"]["promptedge_text_policy"] = {"edge_text_as_prompt": False}

        output = adapt_router_record(row)

        self.assertTrue(output["would_switch"])
        self.assertFalse(output["uses_promptedge_text"])
        self.assertEqual(output["control_variant"], "node_only_no_promptedge_text")

    def test_summary_counts_switches_and_controls(self):
        outputs = [
            adapt_router_record(self._row("switch_to_objective", "C", "a")),
            adapt_router_record(self._row("abstain", "C", "a")),
            adapt_router_record(self._row("switch_to_objective", "D", "b")),
        ]

        summary = summarize_adapter_outputs(outputs)

        self.assertEqual(summary["records"], 3)
        self.assertEqual(summary["would_switch"], 2)
        self.assertEqual(summary["variant_counts"], {"a": 2, "b": 1})


if __name__ == "__main__":
    unittest.main()
