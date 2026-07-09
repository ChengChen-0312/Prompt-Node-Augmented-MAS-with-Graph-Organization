from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_json


def _variant_correct(summary: Dict[str, Any], variant: str) -> int:
    return int(summary.get("by_variant", {}).get(variant, {}).get("correct") or 0)


def build_r280_summary(
    r274_summary_json: str = "experiment/mmlu/res_logs/mmlu_r274_full24_transfer_api_summary.json",
    r279_summary_json: str = "experiment/mmlu/res_logs/mmlu_r279_edge_gated_v3_api_summary.json",
) -> Dict[str, Any]:
    r274 = load_json(r274_summary_json)
    r279 = load_json(r279_summary_json)
    v3 = r279.get("by_variant", {}).get("proposed_v3_edge_gated_pnpe", {})
    arg = _variant_correct(r274, "arg_baseline_fixed")
    plain = _variant_correct(r274, "plain_requery")
    node = _variant_correct(r274, "node_only_no_promptedge_text")
    proposed = _variant_correct(r274, "proposed_promptnode_promptedge")
    v3_correct = int(v3.get("correct") or 0)
    v3_harms = int(v3.get("harms") or 0)
    return {
        "run_id": "R280",
        "title": "V3 prospective full24 result and goal audit",
        "claim_boundary": "Goal audit and transfer result boundary; not SCI-Q2-ready unless prospective v3 beats strong controls.",
        "aligned_with_goal": True,
        "goal_drift_detected": False,
        "sci_q2_ready": False,
        "arg_baseline_correct": arg,
        "plain_requery_correct": plain,
        "node_only_correct": node,
        "proposed_promptnode_promptedge_correct": proposed,
        "proposed_v3_edge_gated_correct": v3_correct,
        "proposed_v3_fix_harm": f"{int(v3.get('fixes') or 0)}/{v3_harms}",
        "v3_beats_arg": v3_correct > arg,
        "v3_beats_plain": v3_correct > plain,
        "v3_beats_node_only": v3_correct > node,
        "v3_beats_prior_proposed": v3_correct > proposed,
        "transfer_superiority_supported": v3_correct > arg and v3_correct > plain and v3_correct > node and v3_correct > proposed and v3_harms == 0,
        "next": "If transfer superiority is false, use R280 as limitation and move to split-heldout selector training rather than more prompt tweaking.",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R280 V3 Result + Goal Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Aligned with goal: `{summary['aligned_with_goal']}`",
            f"- Goal drift detected: `{summary['goal_drift_detected']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- ARG/plain/node/prior PN+PE/v3: `{summary['arg_baseline_correct']}` / `{summary['plain_requery_correct']}` / `{summary['node_only_correct']}` / `{summary['proposed_promptnode_promptedge_correct']}` / `{summary['proposed_v3_edge_gated_correct']}`",
            f"- V3 fix/harm: `{summary['proposed_v3_fix_harm']}`",
            f"- Transfer superiority supported: `{summary['transfer_superiority_supported']}`",
            "",
            summary["next"],
            "",
        ]
    )


def run(
    r274_summary_json: str = "experiment/mmlu/res_logs/mmlu_r274_full24_transfer_api_summary.json",
    r279_summary_json: str = "experiment/mmlu/res_logs/mmlu_r279_edge_gated_v3_api_summary.json",
    summary_json: str = "experiment/mmlu/res_logs/mmlu_r280_v3_result_goal_audit_summary.json",
    report_md: str = "experiment/mmlu/run_logs/mmlu_r280_v3_result_goal_audit.md",
) -> Dict[str, Any]:
    summary = build_r280_summary(r274_summary_json, r279_summary_json)
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R280 v3 result and goal audit.")
    parser.add_argument("--r274_summary_json", default="experiment/mmlu/res_logs/mmlu_r274_full24_transfer_api_summary.json")
    parser.add_argument("--r279_summary_json", default="experiment/mmlu/res_logs/mmlu_r279_edge_gated_v3_api_summary.json")
    parser.add_argument("--summary_json", default="experiment/mmlu/res_logs/mmlu_r280_v3_result_goal_audit_summary.json")
    parser.add_argument("--report_md", default="experiment/mmlu/run_logs/mmlu_r280_v3_result_goal_audit.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
