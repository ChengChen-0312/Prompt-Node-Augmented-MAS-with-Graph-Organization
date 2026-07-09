from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R321_SUMMARY = "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json"
DEFAULT_R381_SUMMARY = "experiment/mmlu/res_logs/mmlu_r381_option_binding_fresh_eval_analysis_summary.json"
DEFAULT_R396_SUMMARY = "experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json"
DEFAULT_R401_SUMMARY = "experiment/mmlu/res_logs/mmlu_r401_contrastive_verifier_targeted_analysis_and_goal_audit_summary.json"
DEFAULT_R402_SUMMARY = "experiment/mmlu/res_logs/mmlu_r402_result_to_claim_synthesis_for_paper_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r405_experiment_integrity_local_precheck_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r405_experiment_integrity_local_precheck_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(_repo_path(path).read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _paper_row(r321: Dict[str, Any], slice_name: str) -> Dict[str, Any]:
    for row in r321.get("paper_main_results", []):
        if row.get("slice") == slice_name:
            return row
    raise KeyError(f"Missing paper_main_results slice: {slice_name}")


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _claim_result(
    claim: Dict[str, Any],
    status: str,
    verified_values: Dict[str, Any],
    expected_values: Dict[str, Any],
    boundary_action: str,
) -> Dict[str, Any]:
    return {
        "id": claim["id"],
        "claim_status": claim["status"],
        "paper_use": claim["paper_use"],
        "source": claim["source"],
        "status": status,
        "verified_values": verified_values,
        "expected_values": expected_values,
        "boundary_action": boundary_action,
    }


def _verify_c1(claim: Dict[str, Any], sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    row = _paper_row(sources["r321"], "AQuA_audit_clean_tail31")
    expected = {"baseline": "28/31", "promptnode": "31/31", "delta_correct": 3}
    verified = {key: row.get(key) for key in expected}
    ok = claim["status"] == "supported" and verified == expected
    return _claim_result(claim, _status(ok), verified, expected, "allow_narrow_main_claim")


def _verify_c2(claim: Dict[str, Any], sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    row = _paper_row(sources["r321"], "MMLU_STEM_main97")
    expected = {"baseline": "88/97", "promptnode": "95/97", "delta_correct": 7, "fix_harm": "7/0"}
    verified = {key: row.get(key) for key in expected}
    ok = claim["status"] == "supported" and verified == expected
    return _claim_result(claim, _status(ok), verified, expected, "allow_narrow_main_claim")


def _verify_c3(claim: Dict[str, Any], sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    r381 = sources["r381"]
    expected = {"records": 24, "arg_correct": 21, "hybrid_correct": 24, "delta_correct": 3, "harms": 0}
    verified = {
        "records": r381.get("records"),
        "arg_correct": r381.get("arg_correct"),
        "hybrid_correct": r381.get("hybrid_correct"),
        "delta_correct": r381.get("delta_correct"),
        "harms": r381.get("harms"),
    }
    ok = claim["status"] == "partial" and verified == expected
    return _claim_result(claim, _status(ok), verified, expected, "appendix_or_mechanism_pilot_only")


def _verify_c4(claim: Dict[str, Any], sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    r396 = sources["r396"]
    expected = {"records": 48, "arg_correct": 41, "hybrid_correct": 41, "delta_correct": 0, "harms": 0}
    verified = {
        "records": r396.get("records"),
        "arg_correct": r396.get("arg_correct"),
        "hybrid_correct": r396.get("hybrid_correct"),
        "delta_correct": r396.get("delta_correct"),
        "harms": r396.get("harms"),
    }
    ok = claim["status"] == "supported" and verified == expected
    return _claim_result(claim, _status(ok), verified, expected, "allow_no_harm_boundary_claim")


def _verify_c5(claim: Dict[str, Any], sources: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    r401 = sources["r401"]
    permissions = r401.get("claim_permissions", {})
    expected = {
        "claim_status": "unsupported",
        "paper_use": "forbidden_claim",
        "integrate_contrastive_path": False,
        "main_paper_claim_allowed": False,
    }
    verified = {
        "claim_status": claim.get("status"),
        "paper_use": claim.get("paper_use"),
        "integrate_contrastive_path": permissions.get("integrate_contrastive_path"),
        "main_paper_claim_allowed": permissions.get("main_paper_claim_allowed"),
    }
    ok = verified == expected
    return _claim_result(claim, _status(ok), verified, expected, "forbid_as_claim")


CLAIM_VERIFIERS: Dict[str, Callable[[Dict[str, Any], Dict[str, Dict[str, Any]]], Dict[str, Any]]] = {
    "C1_aqua_audit_clean_gain": _verify_c1,
    "C2_mmlu_stem_gain": _verify_c2,
    "C3_history_optionbinding_pilot_gain": _verify_c3,
    "C4_mixed_nonmath_no_harm": _verify_c4,
    "C5_broad_general_improvement": _verify_c5,
}


def build_local_precheck(
    r321_summary: str = DEFAULT_R321_SUMMARY,
    r381_summary: str = DEFAULT_R381_SUMMARY,
    r396_summary: str = DEFAULT_R396_SUMMARY,
    r401_summary: str = DEFAULT_R401_SUMMARY,
    r402_summary: str = DEFAULT_R402_SUMMARY,
) -> Dict[str, Any]:
    source_paths = {
        "r321": r321_summary,
        "r381": r381_summary,
        "r396": r396_summary,
        "r401": r401_summary,
        "r402": r402_summary,
    }
    source_file_rows = [
        {"key": key, "path": path, "exists": _repo_path(path).exists()}
        for key, path in source_paths.items()
    ]
    source_files_ok = all(row["exists"] for row in source_file_rows)
    sources = {key: _load_json(path) for key, path in source_paths.items() if _repo_path(path).exists()}
    r402 = sources["r402"]
    claim_checks: List[Dict[str, Any]] = []
    for claim in r402.get("claims", []):
        verifier = CLAIM_VERIFIERS.get(claim["id"])
        if verifier is None:
            claim_checks.append(
                _claim_result(claim, "FAIL", {}, {}, "unknown_claim_requires_manual_review")
            )
            continue
        claim_checks.append(verifier(claim, sources))

    number_consistency_ok = all(row["status"] == "PASS" for row in claim_checks)
    permissions = r402.get("claim_permissions", {})
    overclaim_ok = (
        permissions.get("broad_general_improvement_claim_allowed") is False
        and permissions.get("main_paper_claim_allowed") is False
        and permissions.get("sci_q2_ready") is False
        and any(
            row["id"] == "C5_broad_general_improvement"
            and row["boundary_action"] == "forbid_as_claim"
            and row["status"] == "PASS"
            for row in claim_checks
        )
    )
    local_ok = source_files_ok and number_consistency_ok and overclaim_ok
    return {
        "run_id": "R405",
        "title": "Experiment integrity local precheck",
        "claim_boundary": (
            "R405 is a deterministic local precheck for result existence, number consistency, and claim boundaries. "
            "It does not replace the required independent experiment-audit reviewer."
        ),
        "no_api": True,
        "broad_api": False,
        "local_precheck_status": "pass_external_pending" if local_ok else "fail_external_pending",
        "checks": {
            "source_files_exist": {
                "status": _status(source_files_ok),
                "files": source_file_rows,
            },
            "claim_number_consistency": {
                "status": _status(number_consistency_ok),
                "checked_claims": len(claim_checks),
            },
            "overclaim_boundary": {
                "status": _status(overclaim_ok),
                "broad_general_improvement_claim_allowed": permissions.get("broad_general_improvement_claim_allowed"),
                "main_paper_claim_allowed": permissions.get("main_paper_claim_allowed"),
                "sci_q2_ready": permissions.get("sci_q2_ready"),
            },
        },
        "claim_checks": claim_checks,
        "external_review_required": True,
        "external_reviewer_available_in_this_session": False,
        "integrity_audit_complete": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R406_external_integrity_review_package",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R405 Experiment Integrity Local Precheck",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Local precheck status: `{summary['local_precheck_status']}`",
        f"- External review required: `{summary['external_review_required']}`",
        f"- Integrity audit complete: `{summary['integrity_audit_complete']}`",
        f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
        "",
        "## Checks",
        "",
    ]
    rows.extend(f"- `{name}`: `{payload['status']}`" for name, payload in summary["checks"].items())
    rows.extend(["", "## Claim Checks", ""])
    for claim in summary["claim_checks"]:
        rows.append(
            f"- `{claim['id']}`: `{claim['status']}`; boundary=`{claim['boundary_action']}`; values=`{claim['verified_values']}`"
        )
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r321_summary: str = DEFAULT_R321_SUMMARY,
    r381_summary: str = DEFAULT_R381_SUMMARY,
    r396_summary: str = DEFAULT_R396_SUMMARY,
    r401_summary: str = DEFAULT_R401_SUMMARY,
    r402_summary: str = DEFAULT_R402_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_local_precheck(
        r321_summary=r321_summary,
        r381_summary=r381_summary,
        r396_summary=r396_summary,
        r401_summary=r401_summary,
        r402_summary=r402_summary,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic local integrity precheck for paper claims.")
    parser.add_argument("--r321_summary", default=DEFAULT_R321_SUMMARY)
    parser.add_argument("--r381_summary", default=DEFAULT_R381_SUMMARY)
    parser.add_argument("--r396_summary", default=DEFAULT_R396_SUMMARY)
    parser.add_argument("--r401_summary", default=DEFAULT_R401_SUMMARY)
    parser.add_argument("--r402_summary", default=DEFAULT_R402_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
