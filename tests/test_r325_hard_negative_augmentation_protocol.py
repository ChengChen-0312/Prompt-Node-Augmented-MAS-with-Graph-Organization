import json
import unittest
from pathlib import Path


class TestR325HardNegativeAugmentationProtocol(unittest.TestCase):
    def test_hard_negative_manifest_adds_answer_bearing_false_forward_cases(self):
        from experiment.mmlu.r325_hard_negative_augmentation_protocol import build_hard_negative_summary

        summary = build_hard_negative_summary()

        self.assertEqual(summary["run_id"], "R325")
        self.assertEqual(summary["base_manifest_records"], 234)
        self.assertEqual(summary["hard_negative_records"], 4)
        self.assertEqual(summary["augmented_manifest_records"], 238)
        self.assertTrue(summary["feature_leakage_pass"])
        self.assertEqual(summary["hard_negative_target_forward_counts"], {"false": 4})
        self.assertIn("node_only_no_promptedge_text", summary["hard_negative_source_variants"])
        self.assertIn("plain_requery", summary["hard_negative_source_variants"])
        self.assertFalse(summary["paper_claim_authorized"])
        self.assertFalse(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R326_goal_audit_after_selector_pretraining")

    def test_augmented_manifest_marks_promptedge_text_presence_without_exporting_labels(self):
        from experiment.mmlu.r325_hard_negative_augmentation_protocol import run

        out = Path("experiment/mmlu/run_logs/test_r325_augmented_manifest.jsonl")
        summary = run(
            augmented_manifest_jsonl=str(out),
            summary_json="experiment/mmlu/res_logs/test_r325_summary.json",
            report_md="experiment/mmlu/run_logs/test_r325_report.md",
        )
        rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
        hard_rows = [row for row in rows if row.get("source_run") == "R325"]

        self.assertEqual(len(hard_rows), summary["hard_negative_records"])
        self.assertTrue(all(row["features"]["candidate_has_answer_label"] == 1 for row in hard_rows))
        self.assertTrue(all(row["features"]["promptedge_text_present"] == 0 for row in hard_rows if row["source_variant"] == "node_only_no_promptedge_text"))
        self.assertTrue(all("predicted_answer" not in row for row in hard_rows))
        self.assertTrue(all("true_answer" not in row for row in hard_rows))


if __name__ == "__main__":
    unittest.main()
