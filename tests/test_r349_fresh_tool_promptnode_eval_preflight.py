import json
import unittest
from pathlib import Path


class TestR349FreshToolPromptnodeEvalPreflight(unittest.TestCase):
    def test_preflight_builds_fresh_48_task_manifest_without_label_leakage(self):
        from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import build_fresh_preflight

        api_records, local_records, summary = build_fresh_preflight()

        self.assertEqual(summary["run_id"], "R349")
        self.assertEqual(summary["tasks"], 48)
        self.assertEqual(summary["task_family_counts"], {"mmlu_nonstem": 24, "mmlu_stem": 24})
        self.assertEqual(summary["api_manifest_records"], 48)
        self.assertEqual(summary["local_tool_records"], 48)
        self.assertEqual(summary["overlap_with_excluded_task_count"], 0)
        self.assertTrue(summary["leakage_pass"])
        self.assertFalse(summary["uses_true_answers_in_prompt"])
        self.assertFalse(summary["uses_true_answers_in_tool"])
        self.assertEqual(summary["api_calls_planned"], 48)
        self.assertTrue(summary["api_execution_authorized_next"])
        self.assertEqual(summary["next_required_run"], "R350_goal_audit_after_tool_promptnode_fresh_preflight")
        self.assertTrue(all(row["control_variant"] == "arg_baseline_direct_api" for row in api_records))
        self.assertEqual({row["task_id"] for row in api_records}, {row["task_id"] for row in local_records})

    def test_written_manifest_keeps_eval_labels_out_of_model_prompts(self):
        from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import run

        manifest = Path("experiment/mmlu/run_logs/test_r349_api_manifest.jsonl")
        run(
            api_manifest_jsonl=str(manifest),
            local_tool_jsonl="experiment/mmlu/run_logs/test_r349_local_tool_results.jsonl",
            summary_json="experiment/mmlu/res_logs/test_r349_summary.json",
            report_md="experiment/mmlu/run_logs/test_r349_report.md",
        )
        first = json.loads(manifest.read_text(encoding="utf-8").splitlines()[0])
        prompt = "\n".join(message["content"] for message in first["model_visible_messages"])

        self.assertIn("evaluation_only", first)
        self.assertNotIn("true_answer", prompt)
        self.assertNotIn("evaluation_only", prompt)
        self.assertNotIn(first["task_id"], prompt)


if __name__ == "__main__":
    unittest.main()
