import unittest

from experiment.mmlu.r238_conservative_manifest_export import (
    build_conservative_record,
    build_control_records,
    summarize_records,
)


class TestR238ConservativeManifestExport(unittest.TestCase):
    def _row(self, majority_count=1):
        return {
            "task_id": "task_1",
            "router_action": "switch_to_objective",
            "target_option_label": "B",
            "model_visible_input": {
                "baseline_prediction": "A",
                "objective_prediction": "B",
                "objective_prediction_differs_from_baseline": True,
                "objective_top_score": 3,
                "baseline_direct_majority_count": majority_count,
            },
            "router_final_schema": {
                "allowed_option_labels": ["A", "B", "C", "D", "E", "NONE"],
                "promptedge_text_policy": {"edge_text_as_prompt": True},
            },
        }

    def test_conservative_record_switches_when_policy_allows(self):
        record = build_conservative_record(self._row(majority_count=1), "baseline_consensus_guard_top3")

        self.assertEqual(record["control_variant"], "proposed_conservative_router")
        self.assertEqual(record["router_action"], "switch_to_objective")
        self.assertEqual(record["target_option_label"], "B")

    def test_conservative_record_abstains_when_guard_blocks(self):
        record = build_conservative_record(self._row(majority_count=3), "baseline_consensus_guard_top3")

        self.assertEqual(record["router_action"], "abstain")
        self.assertEqual(record["target_option_label"], "NONE")

    def test_controls_preserve_same_switch_rate_for_node_only(self):
        proposed = [
            build_conservative_record(self._row(majority_count=1), "baseline_consensus_guard_top3"),
            build_conservative_record(self._row(majority_count=3), "baseline_consensus_guard_top3"),
        ]

        controls = build_control_records(proposed, seed=7)

        node_only = [row for row in controls if row["control_variant"] == "node_only_no_promptedge_text"]
        self.assertEqual(sum(row["router_action"] == "switch_to_objective" for row in node_only), 1)
        self.assertFalse(node_only[0]["router_final_schema"]["promptedge_text_policy"]["edge_text_as_prompt"])

    def test_summary_counts_variants_and_switches(self):
        records = [
            build_conservative_record(self._row(majority_count=1), "baseline_consensus_guard_top3"),
            build_conservative_record(self._row(majority_count=3), "baseline_consensus_guard_top3"),
        ]

        summary = summarize_records(records)

        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["switches"], 1)
        self.assertEqual(summary["variant_counts"]["proposed_conservative_router"], 2)


if __name__ == "__main__":
    unittest.main()
