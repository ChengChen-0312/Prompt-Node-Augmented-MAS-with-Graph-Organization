from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R327_SUMMARY = "experiment/mmlu/res_logs/mmlu_r327_augmented_selector_retraining_dry_run_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r328_selector_policy_claim_update_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r328_selector_policy_claim_update_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_selector_claim_update(r327_summary: str = DEFAULT_R327_SUMMARY) -> Dict[str, Any]:
    r327 = _load_json(r327_summary)
    ablations = {row["variant"]: row for row in r327.get("feature_ablation_after_hard_negatives", [])}
    without_edge = ablations.get("no_family_no_promptedge_text_feature", {})
    with_edge = ablations.get("no_family_with_promptedge_text_feature", {})
    return {
        "run_id": "R328",
        "title": "Selector policy claim update",
        "claim_boundary": (
            "R328 updates the claim matrix after the augmented selector dry run. It permits only an offline feasibility "
            "claim for graph-policy learning and a PromptEdge safety-feature claim, not an external accuracy claim."
        ),
        "no_api": True,
        "broad_api": False,
        "evidence": {
            "r327_augmented_selector": {
                "manifest_records": r327.get("manifest_records"),
                "hard_negative_records": r327.get("hard_negative_records"),
                "test_accuracy": r327.get("metrics", {}).get("test", {}).get("accuracy"),
                "test_precision_forward": r327.get("metrics", {}).get("test", {}).get("precision_forward"),
                "test_recall_forward": r327.get("metrics", {}).get("test", {}).get("recall_forward"),
                "forwarded_hard_negative_count": r327.get("forwarded_hard_negative_count"),
            },
            "r327_promptedge_ablation": {
                "false_forward_without_edge_text": without_edge.get("test_false_forward"),
                "false_forward_with_edge_text": with_edge.get("test_false_forward"),
                "promptedge_feature_contribution_identified": r327.get("promptedge_feature_contribution_identified"),
            },
        },
        "selector_claim_permissions": {
            "offline_selector_feasibility_claim_allowed": (
                r327.get("metrics", {}).get("test", {}).get("accuracy") == 1.0
                and r327.get("forwarded_hard_negative_count") == 0
            ),
            "promptedge_safety_feature_claim_allowed": bool(r327.get("promptedge_feature_contribution_identified")),
            "external_accuracy_improvement_claim_allowed": False,
            "api_execution_allowed": False,
            "selector_training_main_result_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_text_guidance": [
            "Describe the selector as a transparent offline graph-policy dry run.",
            "Use it to support that PromptNode type, PromptEdge text, permissions, and lifecycle actions are trainable graph features.",
            "Do not report it as a new MMLU/AQuA accuracy number until a prospective API or held-out replay is run.",
        ],
        "next_required_run": "R329_case_study_extraction",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R328 Selector Policy Claim Update",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Selector Claim Permissions",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["selector_claim_permissions"].items())
    rows.extend(["", "## Paper Text Guidance", ""])
    rows.extend(f"- {item}" for item in summary["paper_text_guidance"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r327_summary: str = DEFAULT_R327_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_selector_claim_update(r327_summary=r327_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R328 selector policy claim update.")
    parser.add_argument("--r327_summary", default=DEFAULT_R327_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
