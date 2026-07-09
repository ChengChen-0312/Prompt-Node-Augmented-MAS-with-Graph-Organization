import unittest

from experiment.mmlu.r221_router_control_manifests import (
    build_control_records,
    summarize_controls,
)


class TestR221RouterControlManifests(unittest.TestCase):
    def _record(self, task_id, action, objective="C"):
        return {
            "task_id": task_id,
            "split_role": "train",
            "router_action": action,
            "target_option_label": objective if action == "switch_to_objective" else "NONE",
            "model_visible_input": {
                "baseline_prediction": "A",
                "objective_prediction": objective,
                "objective_prediction_differs_from_baseline": True,
            },
            "router_final_schema": {
                "schema_version": "r217_non_abstain_router_v1",
                "model_visible_fields": [
                    "policy_input.baseline_prediction",
                    "policy_input.objective_prediction",
                ],
                "forbidden_model_visible_fields": ["task_id", "is_correct", "true_answer"],
                "gold_answer_used": False,
            },
        }

    def test_abstain_only_control_forces_all_records_to_none(self):
        records = [
            self._record("a", "switch_to_objective", "C"),
            self._record("b", "abstain", "D"),
        ]

        control = build_control_records(records, "abstain_only_router")

        self.assertEqual([row["router_action"] for row in control], ["abstain", "abstain"])
        self.assertEqual([row["target_option_label"] for row in control], ["NONE", "NONE"])
        self.assertEqual(control[0]["source_router_action"], "switch_to_objective")
        self.assertEqual(control[0]["control_variant"], "abstain_only_router")

    def test_random_switch_same_rate_preserves_original_switch_count(self):
        records = [
            self._record("a", "switch_to_objective", "A"),
            self._record("b", "switch_to_objective", "B"),
            self._record("c", "abstain", "C"),
            self._record("d", "abstain", "D"),
        ]

        control = build_control_records(records, "random_switch_labels_same_rate", seed=7)

        self.assertEqual(
            sum(row["router_action"] == "switch_to_objective" for row in control),
            2,
        )
        self.assertEqual(len(control), 4)

    def test_always_switch_uses_objective_prediction_when_available(self):
        records = [
            self._record("a", "abstain", "C"),
            self._record("b", "abstain", "D"),
        ]

        control = build_control_records(records, "always_switch_to_objective")

        self.assertEqual([row["router_action"] for row in control], ["switch_to_objective", "switch_to_objective"])
        self.assertEqual([row["target_option_label"] for row in control], ["C", "D"])

    def test_no_edge_text_preserves_labels_but_disables_edge_text_policy(self):
        records = [self._record("a", "switch_to_objective", "C")]

        control = build_control_records(records, "node_only_no_promptedge_text")

        self.assertEqual(control[0]["router_action"], "switch_to_objective")
        self.assertFalse(control[0]["router_final_schema"]["promptedge_text_policy"]["edge_text_as_prompt"])
        self.assertFalse(control[0]["control_policy"]["promptedge_text_enabled"])

    def test_summary_counts_variants_and_switches(self):
        rows = build_control_records(
            [self._record("a", "switch_to_objective", "C")],
            "abstain_only_router",
        )

        summary = summarize_controls({"abstain_only_router": rows})

        self.assertEqual(summary["variants"], 1)
        self.assertEqual(summary["variant_rows"]["abstain_only_router"], 1)
        self.assertEqual(summary["variant_switches"]["abstain_only_router"], 0)


if __name__ == "__main__":
    unittest.main()
