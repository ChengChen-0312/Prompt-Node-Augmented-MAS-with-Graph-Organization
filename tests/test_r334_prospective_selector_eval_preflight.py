import json
import unittest
from pathlib import Path


class TestR334ProspectiveSelectorEvalPreflight(unittest.TestCase):
    def test_preflight_builds_heldout_manifest_with_no_prompt_leakage(self):
        from experiment.mmlu.r334_prospective_selector_eval_preflight import build_preflight_summary

        records, summary = build_preflight_summary()

        self.assertEqual(summary["run_id"], "R334")
        self.assertEqual(summary["tasks"], 48)
        self.assertEqual(summary["records"], 144)
        self.assertEqual(summary["task_family_counts"], {"mmlu_nonstem": 24, "mmlu_stem": 24})
        self.assertEqual(set(summary["variant_counts"]), {"arg_baseline_direct", "selector_promptnode_promptedge_policy", "cost_matched_plain_requery"})
        self.assertEqual(summary["training_overlap_count"], 0)
        self.assertTrue(summary["leakage_pass"])
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R335_prospective_selector_eval_api_smoke")
        self.assertTrue(all("task_id" not in "\n".join(m["content"] for m in row["model_visible_messages"]) for row in records))

    def test_written_manifest_keeps_labels_out_of_prompts(self):
        from experiment.mmlu.r334_prospective_selector_eval_preflight import run

        out = Path("experiment/mmlu/run_logs/test_r334_manifest.jsonl")
        run(
            manifest_jsonl=str(out),
            summary_json="experiment/mmlu/res_logs/test_r334_summary.json",
            report_md="experiment/mmlu/run_logs/test_r334_report.md",
        )
        first = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
        prompt = "\n".join(message["content"] for message in first["model_visible_messages"])

        self.assertIn("evaluation_only", first)
        self.assertNotIn("true_answer", prompt)
        self.assertNotIn("evaluation_only", prompt)


if __name__ == "__main__":
    unittest.main()
