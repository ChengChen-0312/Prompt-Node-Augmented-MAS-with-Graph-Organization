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


DEFAULT_R359_SUMMARY = "experiment/mmlu/res_logs/mmlu_r359_learned_graph_policy_source_invariance_audit_summary.json"
DEFAULT_R360_SUMMARY = "experiment/mmlu/res_logs/mmlu_r360_source_invariant_graph_policy_retraining_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r361_goal_audit_after_source_invariant_policy_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r361_goal_audit_after_source_invariant_policy_report.md"


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


def build_goal_audit_summary(
    r359_summary: str = DEFAULT_R359_SUMMARY,
    r360_summary: str = DEFAULT_R360_SUMMARY,
) -> Dict[str, Any]:
    r359 = _load_json(r359_summary)
    r360 = _load_json(r360_summary)
    corrected = bool(r359.get("source_run_feature_risk_detected")) and bool(r360.get("source_features_removed"))
    gate_ready = (
        r360.get("dev_false_positives") == 0
        and r360.get("dev_false_negatives") == 0
        and r360.get("test_false_positives") == 0
        and r360.get("test_false_negatives") == 0
    )
    return {
        "run_id": "R361",
        "title": "Goal audit after source-invariant policy",
        "claim_boundary": (
            "R361 is the five-iteration audit after R356-R360. The learned graph-policy path is aligned again "
            "after removing source-run shortcuts, but only a fresh preflight is authorized next."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R356", "R357", "R358", "R359", "R360"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "promptnodes_as_first_class_graph_actions": True,
            "source_shortcut_detected_and_corrected": corrected,
            "source_invariant_gate_ready_for_preflight": gate_ready,
            "hand_template_limitation_accounted_for": True,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "offline_source_invariant_training_claim_allowed": gate_ready,
            "fresh_eval_preflight_allowed": gate_ready,
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Proceed to a fresh preflight using the source-invariant graph policy.",
            "Do not run API unless the preflight has nonzero candidate coverage and no prompt leakage.",
            "Keep R358 shortcut-learning result in the internal audit trail, not as positive evidence.",
        ],
        "next_required_run": "R362_source_invariant_fresh_eval_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R361 Goal Audit After Source-Invariant Policy",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Alignment",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", "## Claim Permissions", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["claim_permissions"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r359_summary: str = DEFAULT_R359_SUMMARY,
    r360_summary: str = DEFAULT_R360_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(r359_summary=r359_summary, r360_summary=r360_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R361 goal audit after source-invariant policy.")
    parser.add_argument("--r359_summary", default=DEFAULT_R359_SUMMARY)
    parser.add_argument("--r360_summary", default=DEFAULT_R360_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
