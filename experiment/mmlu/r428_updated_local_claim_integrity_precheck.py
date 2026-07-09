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
DEFAULT_R414 = "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json"
DEFAULT_R426 = "experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r428_updated_local_claim_integrity_precheck_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r428_updated_local_claim_integrity_precheck_report.md"


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


def _claim_check(claim: Dict[str, Any], status: str, verified_values: Dict[str, Any], boundary_action: str) -> Dict[str, Any]:
    return {
        "id": claim.get("id"),
        "claim_status": claim.get("status"),
        "paper_use": claim.get("paper_use"),
        "source": claim.get("source"),
        "status": status,
        "verified_values": verified_values,
        "boundary_action": boundary_action,
    }


def build_updated_local_precheck(
    r415_summary: str = DEFAULT_R415,
    r414_summary: str = DEFAULT_R414,
    r426_summary: str = DEFAULT_R426,
) -> Dict[str, Any]:
    r415 = _load_json(r415_summary)
    r414 = _load_json(r414_summary)
    r426 = _load_json(r426_summary)
    sources = [r415_summary, r414_summary, r426_summary]
    source_rows = [{"path": path, "exists": _repo_path(path).exists()} for path in sources]
    source_ok = all(row["exists"] for row in source_rows)
    claim_checks: List[Dict[str, Any]] = []
    for claim in r415.get("claims", []):
        if claim.get("id") == "C6_definition_challenge_fresh_positive":
            verified = {
                "records": r414.get("records"),
                "arg_correct": r414.get("arg_correct"),
                "hybrid_correct": r414.get("hybrid_correct"),
                "candidate_correct": r414.get("candidate_correct"),
                "fixes": r414.get("fixes"),
                "harms": r414.get("harms"),
                "wrong_forward_count": r414.get("wrong_forward_count"),
            }
            expected = {
                "records": 24,
                "arg_correct": 21,
                "hybrid_correct": 22,
                "candidate_correct": 21,
                "fixes": 1,
                "harms": 0,
                "wrong_forward_count": 0,
            }
            claim_checks.append(
                _claim_check(
                    claim,
                    "PASS" if verified == expected and claim.get("status") == "supported_narrow" else "FAIL",
                    verified,
                    "allow_narrow_targeted_claim_only",
                )
            )
        elif claim.get("id") == "C5_broad_general_improvement":
            claim_checks.append(_claim_check(claim, "PASS", {"status": claim.get("status")}, "forbid_as_claim"))
        else:
            claim_checks.append(_claim_check(claim, "PASS", {"status": claim.get("status")}, "carry_forward_previous_precheck"))
    cost_rows = {row.get("id"): row for row in r426.get("cost_rows", [])}
    cost_row_checks = {}
    stem = cost_rows.get("MMLU_STEM_R306_probe_estimate", {})
    cost_row_checks["MMLU_STEM_R306_probe_estimate"] = {
        "status": "PASS" if stem.get("score") == "95/97" and stem.get("cost_evidence") == "probe_estimate_not_exact" else "FAIL",
        "score": stem.get("score"),
        "cost": stem.get("cost"),
        "cost_evidence": stem.get("cost_evidence"),
    }
    broad_allowed = r415.get("claim_permissions", {}).get("broad_nonmath_claim_allowed") is True
    checks = {
        "source_files_exist": {"status": "PASS" if source_ok else "FAIL", "files": source_rows},
        "claim_number_consistency": {
            "status": "PASS" if all(row["status"] == "PASS" for row in claim_checks) else "FAIL",
            "checked_claims": len(claim_checks),
        },
        "cost_row_consistency": {
            "status": "PASS" if all(row["status"] == "PASS" for row in cost_row_checks.values()) else "FAIL",
            "checked_rows": list(cost_row_checks),
        },
        "overclaim_boundary": {
            "status": "PASS" if not broad_allowed else "FAIL",
            "broad_nonmath_claim_allowed": broad_allowed,
        },
    }
    return {
        "run_id": "R428",
        "title": "Updated local claim integrity precheck",
        "claim_boundary": (
            "R428 mechanically verifies updated C6 and STEM cost-estimate rows. It does not replace external integrity audit."
        ),
        "no_api": True,
        "broad_api": False,
        "checks": checks,
        "claim_checks": claim_checks,
        "cost_row_checks": cost_row_checks,
        "external_review_required": True,
        "integrity_audit_complete": False,
        "paper_draft_authorized_next": all(check["status"] == "PASS" for check in checks.values()),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R429_paper_method_results_draft_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R428 Updated Local Claim Integrity Precheck",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Checks",
        "",
    ]
    rows.extend(f"- `{key}`: `{value['status']}`" for key, value in summary["checks"].items())
    rows.extend(["", f"- Paper draft authorized next: `{summary['paper_draft_authorized_next']}`", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r415_summary: str = DEFAULT_R415,
    r414_summary: str = DEFAULT_R414,
    r426_summary: str = DEFAULT_R426,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_updated_local_precheck(
        r415_summary=r415_summary,
        r414_summary=r414_summary,
        r426_summary=r426_summary,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run updated local claim integrity precheck.")
    parser.add_argument("--r415_summary", default=DEFAULT_R415)
    parser.add_argument("--r414_summary", default=DEFAULT_R414)
    parser.add_argument("--r426_summary", default=DEFAULT_R426)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
