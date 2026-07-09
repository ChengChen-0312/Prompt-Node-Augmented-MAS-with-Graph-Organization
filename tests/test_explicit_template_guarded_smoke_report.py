import json
import tempfile
import unittest
from pathlib import Path


class ExplicitTemplateGuardedSmokeReportTests(unittest.TestCase):
    def test_summary_requires_promptnode_evidence_and_clean_fix_before_broad_api(self):
        from experiment.aqua.explicit_template_guarded_smoke_report import (
            build_explicit_template_guarded_smoke_summary,
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            baseline = tmpdir / "baseline.jsonl"
            forced = tmpdir / "forced.jsonl"
            plan = tmpdir / "plan.jsonl"
            audit = tmpdir / "audit.jsonl"

            baseline_rows = [
                {"task_id": "task_8", "predicted_answer": "E", "true_answer": "E", "is_solved": True},
                {"task_id": "task_108", "predicted_answer": "B", "true_answer": "D", "is_solved": False},
                {"task_id": "task_188", "predicted_answer": "D", "true_answer": "D", "is_solved": True},
                {"task_id": "task_250", "predicted_answer": "A", "true_answer": "E", "is_solved": False},
            ]
            forced_rows = [
                {
                    "task_id": "task_108",
                    "predicted_answer": "D",
                    "true_answer": "D",
                    "is_solved": True,
                    "generated_graph": {"roles": ["Math Solver", "PN_Memory", "PN_Verifier", "PN_Router"]},
                    "selected_candidate_index": 0,
                    "candidate_graphs": [{"rank": 1, "support_count": 35}],
                },
                {
                    "task_id": "task_250",
                    "predicted_answer": "A",
                    "true_answer": "E",
                    "is_solved": False,
                    "generated_graph": {"roles": ["Math Solver", "PN_Memory", "PN_Verifier", "PN_Router"]},
                    "selected_candidate_index": 0,
                    "candidate_graphs": [{"rank": 1, "support_count": 35}],
                },
            ]
            template = {
                "rank": 1,
                "prompt_node_roles": ["PN_Memory", "PN_Verifier", "PN_Router"],
                "prompt_node_specs": [
                    {"identity_type": "Memory", "permissions": ["read"], "budget": {"max_tokens": 1}, "lifecycle_actions": ["update"], "content_schema": {"kept_fields": []}, "insertion_pattern": "memory_bridge"},
                    {"identity_type": "Instruction/Verifier", "permissions": ["read"], "budget": {"max_tokens": 1}, "lifecycle_actions": ["update"], "content_schema": {"kept_fields": []}, "insertion_pattern": "aggregator_checkpoint"},
                    {"identity_type": "Agent-like", "permissions": ["forward"], "budget": {"max_tokens": 1}, "lifecycle_actions": ["update"], "content_schema": {"kept_fields": []}, "insertion_pattern": "router"},
                ],
                "graph": {"edge_permissions": {"PN_Verifier->PN_Router": ["forward"]}},
            }
            plan_rows = [
                {"task_id": "task_8", "target_action": "fallback_to_arg", "requires_api_execution": False, "selector_input": {}},
                {"task_id": "task_108", "target_action": "switch_to_objective", "requires_api_execution": True, "selected_template": template, "selector_input": {"objective_top_score": 3}},
                {"task_id": "task_188", "target_action": "fallback_to_arg", "requires_api_execution": False, "selector_input": {}},
                {"task_id": "task_250", "target_action": "switch_to_objective", "requires_api_execution": True, "selected_template": template, "selector_input": {"objective_top_score": 3}},
            ]
            audit_rows = [
                {"task_id": "task_8", "audit_label": "clean"},
                {"task_id": "task_108", "audit_label": "noisy"},
                {"task_id": "task_188", "audit_label": "clean"},
                {"task_id": "task_250", "audit_label": "clean"},
            ]
            for path, rows in [(baseline, baseline_rows), (forced, forced_rows), (plan, plan_rows), (audit, audit_rows)]:
                path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            summary = build_explicit_template_guarded_smoke_summary(
                baseline_jsonl=str(baseline),
                forced_jsonl=str(forced),
                r097_plan_jsonl=str(plan),
                audit_file=str(audit),
            )

        self.assertEqual(summary["rule"], "r124_explicit_template_guarded_smoke")
        self.assertEqual(summary["total_tasks"], 4)
        self.assertEqual(summary["baseline_accuracy"], "2/4")
        self.assertEqual(summary["selected_accuracy"], "3/4")
        self.assertEqual(summary["switch_tasks"], ["task_108", "task_250"])
        self.assertEqual(summary["fallback_tasks"], ["task_8", "task_188"])
        self.assertEqual(summary["promptnode_graph_evidence_on_switches"], "2/2")
        self.assertEqual(summary["switch_update2_metadata"], "2/2")
        self.assertEqual(summary["fix_harm"], "1/0")
        self.assertEqual(summary["clean_fix_harm"], "0/0")
        self.assertEqual(summary["noisy_fix_harm"], "1/0")
        fallback_rows = [row for row in summary["rows"] if row["selected_source"] == "baseline"]
        self.assertTrue(fallback_rows)
        self.assertTrue(all(row["selected_template_rank"] is None for row in fallback_rows))
        self.assertFalse(summary["broad_api_allowed_next"])
        self.assertEqual(
            summary["claim_boundary"],
            "same-four-task explicit-template guarded smoke; broader claims require the smoke gate to pass",
        )


if __name__ == "__main__":
    unittest.main()
