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


def build_r277_summary(
    r276_summary_json: str = "experiment/mmlu/res_logs/mmlu_r276_edge_gated_transfer_selector_summary.json",
) -> Dict[str, Any]:
    r276 = load_json(r276_summary_json)
    if r276.get("beats_arg") and r276.get("no_harm"):
        claim_supported = "partial"
        revision = "PromptEdge should be framed as a gated/prunable edge; full24 replay supports a prospective selector, not final transfer superiority."
    else:
        claim_supported = "no"
        revision = "Do not claim transfer improvement; keep transfer as limitation and return to prospective selector design."
    return {
        "run_id": "R277",
        "title": "Transfer claim update after full24 edge-gated selector",
        "claim_boundary": "Claim update only; no API and no new accuracy claim.",
        "claim_supported": claim_supported,
        "sci_q2_ready": False,
        "r276_correct": r276.get("correct"),
        "r276_records": r276.get("records"),
        "r276_fix_harm": r276.get("fix_harm"),
        "beats_arg": r276.get("beats_arg"),
        "beats_plain_requery": r276.get("beats_plain_requery"),
        "beats_node_only": r276.get("beats_node_only"),
        "beats_proposed": r276.get("beats_proposed"),
        "suggested_claim_revision": revision,
        "next_experiments_needed": [
            "Prospective full24 or transfer100 run with the edge-gated policy in the prompt, not post-hoc replay.",
            "A held-out split for selector rule selection vs evaluation to avoid tiny/full24 overfitting.",
            "Negative controls: always-plain, always-node, always-promptedge, random-gated edge.",
        ],
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R277 Transfer Claim Update",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Claim supported: `{summary['claim_supported']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        f"- R276 correct/fix-harm: `{summary['r276_correct']}` / `{summary['r276_fix_harm']}`",
        f"- Beats ARG/plain/node/proposed: `{summary['beats_arg']}` / `{summary['beats_plain_requery']}` / `{summary['beats_node_only']}` / `{summary['beats_proposed']}`",
        "",
        "## Suggested Claim Revision",
        "",
        summary["suggested_claim_revision"],
        "",
        "## Next Experiments Needed",
        "",
    ]
    rows.extend(f"- {item}" for item in summary["next_experiments_needed"])
    rows.append("")
    return "\n".join(rows)


def run(
    r276_summary_json: str = "experiment/mmlu/res_logs/mmlu_r276_edge_gated_transfer_selector_summary.json",
    summary_json: str = "experiment/mmlu/res_logs/mmlu_r277_transfer_claim_update_summary.json",
    report_md: str = "experiment/mmlu/run_logs/mmlu_r277_transfer_claim_update.md",
) -> Dict[str, Any]:
    summary = build_r277_summary(r276_summary_json)
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update transfer claim after R276.")
    parser.add_argument("--r276_summary_json", default="experiment/mmlu/res_logs/mmlu_r276_edge_gated_transfer_selector_summary.json")
    parser.add_argument("--summary_json", default="experiment/mmlu/res_logs/mmlu_r277_transfer_claim_update_summary.json")
    parser.add_argument("--report_md", default="experiment/mmlu/run_logs/mmlu_r277_transfer_claim_update.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
