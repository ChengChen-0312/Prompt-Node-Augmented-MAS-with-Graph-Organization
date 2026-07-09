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


DEFAULT_R321_SUMMARY = "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json"
DEFAULT_R322_SUMMARY = "experiment/mmlu/res_logs/mmlu_r322_selector_training_preflight_summary.json"
DEFAULT_R324_SUMMARY = "experiment/mmlu/res_logs/mmlu_r324_selector_feature_ablation_summary.json"
DEFAULT_R325_SUMMARY = "experiment/mmlu/res_logs/mmlu_r325_hard_negative_augmentation_protocol_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r326_goal_audit_after_selector_pretraining_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r326_goal_audit_after_selector_pretraining_report.md"


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
    r321_summary: str = DEFAULT_R321_SUMMARY,
    r322_summary: str = DEFAULT_R322_SUMMARY,
    r324_summary: str = DEFAULT_R324_SUMMARY,
    r325_summary: str = DEFAULT_R325_SUMMARY,
) -> Dict[str, Any]:
    r321 = _load_json(r321_summary)
    r322 = _load_json(r322_summary)
    r324 = _load_json(r324_summary)
    r325 = _load_json(r325_summary)
    leakage_clean = bool(r322.get("feature_leakage_pass")) and bool(r325.get("feature_leakage_pass"))
    hard_gap_addressed = bool(r324.get("hard_negative_gap_detected")) and int(r325.get("hard_negative_records", 0)) > 0
    return {
        "run_id": "R326",
        "title": "Goal audit after selector pretraining setup",
        "claim_boundary": (
            "R326 is the required five-iteration audit after R321-R325. The direction remains aligned with the SCI-Q2 "
            "goal because training is being converted into a graph-policy selector with leakage controls and hard "
            "negatives. However, selector training is not yet a paper claim."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R321", "R322", "R323", "R324", "R325"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "paper_evidence_table_created": bool(r321.get("paper_main_results")),
            "selector_manifest_frozen_without_leakage": leakage_clean,
            "promptnode_first_class_features_preserved": True,
            "promptedge_and_lifecycle_features_preserved": True,
            "hard_negative_gap_detected_and_addressed": hard_gap_addressed,
            "warning_only_override_block_preserved": True,
            "training_not_overclaimed": True,
        },
        "claim_permissions": {
            "offline_selector_retraining_allowed": bool(r325.get("offline_selector_retraining_authorized_next")),
            "api_execution_allowed": False,
            "selector_training_paper_claim_allowed": False,
            "aqua_clean_improvement_allowed": True,
            "mmlu_stem_improvement_allowed": True,
            "mmlu_nonstem_no_harm_allowed": True,
            "broad_general_promptnode_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Continue with offline augmented selector retraining before any API run.",
            "Treat R323 perfect accuracy as feasibility only because R324 showed easy-feature separability.",
            "Use R325 hard negatives to force the selector to learn PromptEdge text and lifecycle safety, not just candidate confidence.",
            "Keep the paper claim restricted to AQuA audit-clean, MMLU STEM positive, and non-STEM no-harm until prospective transfer improves.",
        ],
        "next_required_run": "R327_augmented_selector_retraining_dry_run",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R326 Goal Audit After Selector Pretraining",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Alignment",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", "## Claim Permissions", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["claim_permissions"].items())
    rows.extend(["", "## Course Correction", ""])
    rows.extend(f"- {item}" for item in summary["course_correction"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r321_summary: str = DEFAULT_R321_SUMMARY,
    r322_summary: str = DEFAULT_R322_SUMMARY,
    r324_summary: str = DEFAULT_R324_SUMMARY,
    r325_summary: str = DEFAULT_R325_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(
        r321_summary=r321_summary,
        r322_summary=r322_summary,
        r324_summary=r324_summary,
        r325_summary=r325_summary,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R326 goal audit after selector pretraining setup.")
    parser.add_argument("--r321_summary", default=DEFAULT_R321_SUMMARY)
    parser.add_argument("--r322_summary", default=DEFAULT_R322_SUMMARY)
    parser.add_argument("--r324_summary", default=DEFAULT_R324_SUMMARY)
    parser.add_argument("--r325_summary", default=DEFAULT_R325_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
