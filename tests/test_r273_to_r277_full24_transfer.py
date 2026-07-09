import json
import tempfile
import unittest
from pathlib import Path

from experiment.mmlu.r273_full24_transfer_preflight import build_r273_records, summarize_r273
from experiment.mmlu.r276_edge_gated_transfer_selector import (
    apply_edge_gated_selector,
    build_task_variant_lookup,
    option_binding_surface,
    summarize_selector_records,
)
from experiment.mmlu.r277_transfer_claim_update import build_r277_summary
from experiment.mmlu.r278_edge_gated_v3_preflight import (
    build_v3_records,
    scan_v3_prompt_leakage,
    summarize_v3_preflight,
)
from experiment.mmlu.r279_edge_gated_v3_api_executor import apply_v3_response, parse_v3_response


def _row(task_id, variant, pred, true="C", arg="A", question="Q?\nOption A: 1\nOption B: 2\nOption C: 3\nOption D: 4"):
    return {
        "task_id": task_id,
        "control_variant": variant,
        "selection_role": "arg_error",
        "model_visible_input": {"question": question, "subject": "math"},
        "evaluation_only": {"true_answer": true, "arg_prediction": arg, "arg_error": arg != true},
        "true_answer": true,
        "arg_prediction": arg,
        "predicted_answer": pred,
        "is_correct": pred == true,
        "fix": arg != true and pred == true,
        "harm": arg == true and pred != true,
    }


class TestR273ToR277Full24Transfer(unittest.TestCase):
    def test_r273_records_use_full24_and_balanced_variants(self):
        probe = [
            {
                "task_id": "mmlu-1",
                "features": {"subject": "math"},
                "labels": {"predicted_answer": "A", "true_answer": "C", "arg_error": True},
                "selection_role": "arg_error",
            }
        ]
        source = [
            {
                "task_id": "mmlu-1",
                "subject": "math",
                "question": "Q?\nOption A: 1\nOption B: 2\nOption C: 3\nOption D: 4",
                "predicted_answer": "A",
                "true_answer": "C",
                "is_correct": False,
            }
        ]

        records = build_r273_records(probe, source)
        summary = summarize_r273(records, cost_cap=0.5)

        self.assertEqual(summary["tasks"], 1)
        self.assertEqual(summary["api_required"], 3)
        self.assertTrue(summary["preflight_pass"])
        self.assertEqual({row["run_id"] for row in records}, {"R273"})

    def test_edge_gated_selector_switches_on_unanimous_api_consensus(self):
        rows = [
            _row("t1", "arg_baseline_fixed", "A"),
            _row("t1", "plain_requery", "C"),
            _row("t1", "node_only_no_promptedge_text", "C"),
            _row("t1", "proposed_promptnode_promptedge", "C"),
        ]

        selected = apply_edge_gated_selector("t1", build_task_variant_lookup(rows)["t1"])

        self.assertEqual(selected["predicted_answer"], "C")
        self.assertEqual(selected["decision_rule"], "switch_unanimous_api_views")
        self.assertTrue(selected["fix"])

    def test_edge_gated_selector_prunes_promptedge_when_plain_and_node_agree(self):
        rows = [
            _row("t2", "arg_baseline_fixed", "A", true="D", arg="A"),
            _row("t2", "plain_requery", "D", true="D", arg="A"),
            _row("t2", "node_only_no_promptedge_text", "D", true="D", arg="A"),
            _row("t2", "proposed_promptnode_promptedge", "A", true="D", arg="A"),
        ]

        selected = apply_edge_gated_selector("t2", build_task_variant_lookup(rows)["t2"])

        self.assertEqual(selected["predicted_answer"], "D")
        self.assertEqual(selected["decision_rule"], "switch_plain_node_agree_prune_promptedge")
        self.assertIn("prune", selected["lifecycle_actions"])

    def test_graph_family_switch_requires_option_binding_surface(self):
        rows = [
            _row("t3", "arg_baseline_fixed", "A", true="D", arg="A", question="Which expression matches the total?\nOption A: 1+2\nOption D: 7-3"),
            _row("t3", "plain_requery", "A", true="D", arg="A", question="Which expression matches the total?\nOption A: 1+2\nOption D: 7-3"),
            _row("t3", "node_only_no_promptedge_text", "D", true="D", arg="A", question="Which expression matches the total?\nOption A: 1+2\nOption D: 7-3"),
            _row("t3", "proposed_promptnode_promptedge", "D", true="D", arg="A", question="Which expression matches the total?\nOption A: 1+2\nOption D: 7-3"),
        ]
        selected = apply_edge_gated_selector("t3", build_task_variant_lookup(rows)["t3"])
        self.assertEqual(selected["decision_rule"], "switch_graph_family_option_binding")
        self.assertTrue(option_binding_surface(rows[0]["model_visible_input"]["question"]))

        non_symbolic = [
            _row("t4", "arg_baseline_fixed", "B", true="D", arg="B", question="Bow waves are produced by waves of water\nOption A: overlapping\nOption B: interfering\nOption D: All"),
            _row("t4", "plain_requery", "D", true="D", arg="B", question="Bow waves are produced by waves of water\nOption A: overlapping\nOption B: interfering\nOption D: All"),
            _row("t4", "node_only_no_promptedge_text", "A", true="D", arg="B", question="Bow waves are produced by waves of water\nOption A: overlapping\nOption B: interfering\nOption D: All"),
            _row("t4", "proposed_promptnode_promptedge", "A", true="D", arg="B", question="Bow waves are produced by waves of water\nOption A: overlapping\nOption B: interfering\nOption D: All"),
        ]
        kept = apply_edge_gated_selector("t4", build_task_variant_lookup(non_symbolic)["t4"])
        self.assertEqual(kept["decision_rule"], "keep_arg_unresolved_view_conflict")

    def test_selector_summary_and_r277_claim_boundary(self):
        rows = [
            _row("t1", "arg_baseline_fixed", "A"),
            _row("t1", "plain_requery", "C"),
            _row("t1", "node_only_no_promptedge_text", "C"),
            _row("t1", "proposed_promptnode_promptedge", "C"),
        ]
        selected = [apply_edge_gated_selector("t1", build_task_variant_lookup(rows)["t1"])]
        summary = summarize_selector_records(selected, baseline_correct=0, plain_correct=1, node_correct=1, proposed_correct=1)

        with tempfile.TemporaryDirectory() as tmp:
            r276_path = Path(tmp) / "r276.json"
            r276_path.write_text(json.dumps(summary), encoding="utf-8")
            r277 = build_r277_summary(str(r276_path))

        self.assertEqual(r277["run_id"], "R277")
        self.assertFalse(r277["sci_q2_ready"])
        self.assertIn(r277["claim_supported"], {"partial", "no"})

    def test_r278_v3_preflight_is_leakage_safe(self):
        probe = [
            {
                "task_id": "mmlu-1",
                "features": {"subject": "math"},
                "labels": {"predicted_answer": "A", "true_answer": "C", "arg_error": True},
                "selection_role": "arg_error",
            }
        ]
        source = [
            {
                "task_id": "mmlu-1",
                "subject": "math",
                "question": "Which expression matches?\nOption A: 1+1\nOption C: 2+2",
                "predicted_answer": "A",
                "true_answer": "C",
                "is_correct": False,
            }
        ]

        records = build_v3_records(probe, source)
        summary = summarize_v3_preflight(records, cost_cap=0.2)
        proposed = [row for row in records if row["control_variant"] == "proposed_v3_edge_gated_pnpe"][0]

        self.assertEqual(summary["tasks"], 1)
        self.assertEqual(summary["api_required"], 1)
        self.assertTrue(summary["preflight_pass"])
        self.assertEqual(scan_v3_prompt_leakage(proposed)["leakage_violations"], 0)
        self.assertIn("PN_EdgeGate", proposed["model_visible_messages"][1]["content"])

    def test_r279_parse_and_apply_v3_switch(self):
        parsed = parse_v3_response(
            '{"action":"SWITCH","final_label":"C","independent_label":"C","confidence":"high","edge_decision":"forward","evidence_checks":["x","y"],"lifecycle_actions":["write","forward"]}'
        )
        self.assertEqual(parsed["action"], "SWITCH")
        self.assertEqual(parsed["final_label"], "C")

        row = {
            "task_id": "mmlu-1",
            "control_variant": "proposed_v3_edge_gated_pnpe",
            "api_required": True,
            "evaluation_only": {"true_answer": "C", "arg_prediction": "A", "arg_error": True},
        }
        scored = apply_v3_response(row, '{"action":"SWITCH","final_label":"C","confidence":"high"}', True)
        self.assertEqual(scored["predicted_answer"], "C")
        self.assertTrue(scored["fix"])


if __name__ == "__main__":
    unittest.main()
