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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r456_next_goal_audit_or_external_review_decision_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r456_next_goal_audit_or_external_review_decision_report.md"
AUDITED_RUNS = ["R452", "R453", "R454", "R455", "R456"]


SUMMARY_PATHS = {
    "R452": "experiment/mmlu/res_logs/mmlu_r452_five_run_goal_audit_and_compile_probe_summary.json",
    "R453": "experiment/mmlu/res_logs/mmlu_r453_appendix_noise_audit_pack_summary.json",
    "R454": "experiment/mmlu/res_logs/mmlu_r454_reproducibility_artifact_index_summary.json",
    "R455": "experiment/mmlu/res_logs/mmlu_r455_full_local_smoke_after_appendix_artifact_summary.json",
}


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    target = _repo_path(path)
    return json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R456 Next Goal Audit Or External Review Decision",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Audited runs: `{', '.join(summary['audited_runs'])}`",
        f"- Deviation detected: `{summary['deviation_detected']}`",
        f"- External review decision: `{summary['external_review_execution_decision']}`",
        f"- External transmission allowed now: `{summary['external_transmission_allowed_now']}`",
        f"- Can continue local work: `{summary['can_continue_local_work']}`",
        "",
        "## Decision Rationale",
        "",
    ]
    rows.extend(f"- {item}" for item in summary["decision_rationale"])
    rows.extend(
        [
            "",
            f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )
    return "\n".join(rows)


def run_decision(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    recent = {run_id: _load_json(path) for run_id, path in SUMMARY_PATHS.items()}
    unauthorized = [
        run_id
        for run_id, payload in recent.items()
        if payload.get("paper_claim_authorized") or payload.get("sci_q2_ready")
    ]
    summary: Dict[str, Any] = {
        "run_id": "R456",
        "title": "Next goal audit or external review decision",
        "claim_boundary": (
            "R456 records the next execution decision after R452-R455. It does not transmit local unpublished "
            "material, execute external audits, or certify submission readiness."
        ),
        "no_api": True,
        "broad_api": False,
        "audited_runs": AUDITED_RUNS,
        "audited_summary_paths": SUMMARY_PATHS,
        "goal_alignment_tags": [
            "sci_q2_submission",
            "promptnode_graph_organization",
            "audit_clean_integrity",
            "reproducibility_artifacts",
            "external_review_safety",
        ],
        "unauthorized_claim_runs": unauthorized,
        "deviation_detected": bool(unauthorized),
        "external_review_execution_decision": "defer_until_user_confirms_transmission",
        "external_transmission_allowed_now": False,
        "requires_confirmation_before_transmission": True,
        "can_continue_local_work": True,
        "decision_rationale": [
            "External experiment, paper-claim, and citation audits remain P0 before final claim authorization.",
            "R445 payloads contain unpublished manuscript/result material, so they should not be sent without fresh explicit confirmation.",
            "Local work can continue on static manuscript integrity, reproducibility, and formatting gaps.",
            "Recent runs preserve the core SCI-Q2 goal and keep PromptNode positioned as graph organization rather than a dataset patch.",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R457_static_manuscript_audit_after_appendix",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decide whether to run external audit or continue local work.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_decision(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
