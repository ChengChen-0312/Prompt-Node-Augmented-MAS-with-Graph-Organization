import json
import unittest
from pathlib import Path


class TestR322SelectorTrainingPreflight(unittest.TestCase):
    def test_training_manifest_is_frozen_without_label_or_task_leakage(self):
        from experiment.mmlu.r322_selector_training_preflight import build_selector_preflight_summary

        summary = build_selector_preflight_summary()

        self.assertEqual(summary["run_id"], "R322")
        self.assertEqual(summary["manifest_records"], 234)
        self.assertEqual(summary["positive_forward_targets"], 7)
        self.assertEqual(summary["excluded_audit_items_count"], 3)
        self.assertTrue(summary["feature_leakage_pass"])
        self.assertEqual(summary["feature_leakage_violations"], [])
        self.assertGreater(summary["split_counts"]["train"], 0)
        self.assertGreater(summary["split_counts"]["dev"], 0)
        self.assertGreater(summary["split_counts"]["test"], 0)
        self.assertGreater(summary["positive_split_counts"]["train"], 0)
        self.assertGreater(summary["positive_split_counts"]["dev"], 0)
        self.assertGreater(summary["positive_split_counts"]["test"], 0)
        self.assertTrue(summary["offline_selector_training_authorized_next"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R323_selector_model_dry_run")

    def test_manifest_rows_do_not_export_forbidden_feature_keys(self):
        from experiment.mmlu.r322_selector_training_preflight import run

        out = Path("experiment/mmlu/run_logs/test_r322_selector_manifest.jsonl")
        summary = run(manifest_jsonl=str(out), summary_json="experiment/mmlu/res_logs/test_r322_summary.json", report_md="experiment/mmlu/run_logs/test_r322_report.md")
        forbidden = set(summary["forbidden_feature_keys"])
        first = json.loads(out.read_text(encoding="utf-8").splitlines()[0])

        self.assertNotIn("task_id", first)
        self.assertNotIn("question", first)
        self.assertTrue(forbidden.isdisjoint(first["features"]))
        self.assertIn("promptedge_has_forward", first["features"])
        self.assertIn("promptnode_family", first["features"])


if __name__ == "__main__":
    unittest.main()
