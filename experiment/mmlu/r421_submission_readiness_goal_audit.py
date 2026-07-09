from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R415 = "experiment/mmlu/res_logs/mmlu_r415_update_claim_matrix_after_nonmath_positive_summary.json"
DEFAULT_R416 = "experiment/mmlu/res_logs/mmlu_r416_cost_normalized_claim_table_and_goal_audit_summary.json"
DEFAULT_R420 = "experiment/mmlu/res_logs/mmlu_r420_paper_asset_table_refresh_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r421_submission_readiness_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r421_submission_readiness_goal_audit_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_submission_readiness_audit(
    r415_summary: str = DEFAULT_R415,
    r416_summary: str = DEFAULT_R416,
    r420_summary: str = DEFAULT_R420,
) -> Dict[str, Any]:
    r415 = _load_json(r415_summary)
    r416 = _load_json(r416_summary)
    r420 = _load_json(r420_summary)
    claims = r415.get("claims", [])
    supported_or_narrow = [
        claim.get("id")
        for claim in claims
        if claim.get("status") in {"supported", "supported_narrow", "partial"}
    ]
    blocking_gaps: List[str] = []
    if "independent_integrity_audit_missing" in r416.get("missing_cost_evidence", []) or "external_experiment_integrity_audit" in r420.get("missing_assets", []):
        blocking_gaps.append("external_integrity_audit_missing")
    if "MMLU_STEM_cost_missing" in r416.get("missing_cost_evidence", []):
        blocking_gaps.append("mmlu_stem_cost_missing")
    if not r415.get("claim_permissions", {}).get("broad_nonmath_claim_allowed", False):
        blocking_gaps.append("broad_nonmath_larger_split_missing")
    if "submission_complete_cost_table" in r420.get("missing_assets", []):
        blocking_gaps.append("submission_complete_cost_table_missing")
    return {
        "run_id": "R421",
        "title": "Submission readiness goal audit",
        "claim_boundary": (
            "R421 audits readiness against the SCI-Q2 goal after R417-R421. It is a routing checkpoint, not a claim."
        ),
        "no_api": True,
        "broad_api": False,
        "readiness_verdict": "not_ready" if blocking_gaps else "ready_for_external_review",
        "supported_or_narrow_claims": supported_or_narrow,
        "blocking_gaps": blocking_gaps,
        "iterations_since_last_goal_check": ["R417", "R418", "R419", "R420", "R421"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_designer_remains_main_baseline": True,
            "promptnode_first_class_boundary_preserved": True,
            "heldout_positive_evidence_exists": True,
            "case_study_and_lifecycle_assets_exist": True,
            "cost_reporting_gap_visible": True,
            "overclaiming_blocked": True,
        },
        "recommended_next_actions": [
            "Reconstruct or rerun MMLU STEM cost accounting.",
            "Run independent experiment integrity audit.",
            "Only after those, draft paper tables and methods text.",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R422_mmlu_stem_cost_reconstruction_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R421 Submission Readiness Goal Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Readiness verdict: `{summary['readiness_verdict']}`",
        f"- Supported/narrow claims: `{summary['supported_or_narrow_claims']}`",
        "",
        "## Blocking Gaps",
        "",
    ]
    rows.extend(f"- `{gap}`" for gap in summary["blocking_gaps"])
    rows.extend(["", "## Goal Alignment", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", "## Recommended Next Actions", ""])
    rows.extend(f"- {item}" for item in summary["recommended_next_actions"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r415_summary: str = DEFAULT_R415,
    r416_summary: str = DEFAULT_R416,
    r420_summary: str = DEFAULT_R420,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_submission_readiness_audit(
        r415_summary=r415_summary,
        r416_summary=r416_summary,
        r420_summary=r420_summary,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R421 submission readiness goal audit.")
    parser.add_argument("--r415_summary", default=DEFAULT_R415)
    parser.add_argument("--r416_summary", default=DEFAULT_R416)
    parser.add_argument("--r420_summary", default=DEFAULT_R420)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
