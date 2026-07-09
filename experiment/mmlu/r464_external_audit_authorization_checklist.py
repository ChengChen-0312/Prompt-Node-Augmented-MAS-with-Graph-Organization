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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r464_external_audit_authorization_checklist_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r464_external_audit_authorization_checklist_report.md"
DEFAULT_CHECKLIST_MD = "paper/artifacts/external_audit_authorization_checklist.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _payloads() -> Dict[str, Dict[str, str]]:
    return {
        "experiment_integrity_audit": {
            "payload_md": "experiment/mmlu/run_logs/mmlu_r445_experiment_integrity_external_payload.md",
            "expected_review_md": "experiment/mmlu/run_logs/mmlu_r445_experiment_integrity_external_review.md",
            "purpose": "Check result provenance, no fake ground truth, no phantom results, and claim scope.",
        },
        "paper_claim_audit": {
            "payload_md": "experiment/mmlu/run_logs/mmlu_r445_paper_claim_external_payload.md",
            "expected_review_md": "experiment/mmlu/run_logs/mmlu_r445_paper_claim_external_review.md",
            "purpose": "Check every number/comparison in the manuscript against raw/result files.",
        },
        "citation_context_audit": {
            "payload_md": "experiment/mmlu/run_logs/mmlu_r445_citation_context_external_payload.md",
            "expected_review_md": "experiment/mmlu/run_logs/mmlu_r445_citation_context_external_review.md",
            "purpose": "Check citation metadata and whether citation contexts are supported.",
        },
    }


def render_checklist(summary: Dict[str, Any]) -> str:
    rows = [
        "# External Audit Authorization Checklist",
        "",
        "These payloads contain unpublished manuscript and result material. Do not transmit them to a browser, API, or external reviewer without explicit user confirmation.",
        "",
        f"- Transmission performed: `{summary['transmission_performed']}`",
        f"- Requires confirmation before transmission: `{summary['requires_user_confirmation_before_transmission']}`",
        "",
        "## Payloads",
        "",
    ]
    for name, item in summary["audit_payloads"].items():
        rows.extend(
            [
                f"### {name}",
                "",
                f"- Payload: `{item['payload_md']}`",
                f"- Expected review output: `{item['expected_review_md']}`",
                f"- Purpose: {item['purpose']}",
                "",
            ]
        )
    rows.extend(["## Confirmation Boundary", ""])
    rows.extend(f"- {line}" for line in summary["confirmation_boundary"])
    rows.append("")
    return "\n".join(rows)


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R464 External Audit Authorization Checklist",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Checklist: `{summary['checklist_md']}`",
        f"- Payload count: `{len(summary['audit_payloads'])}`",
        f"- Transmission performed: `{summary['transmission_performed']}`",
        "",
        f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run_checklist(
    checklist_md: str = DEFAULT_CHECKLIST_MD,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    audit_payloads = _payloads()
    summary: Dict[str, Any] = {
        "run_id": "R464",
        "title": "External audit authorization checklist",
        "claim_boundary": (
            "R464 records what would be sent for external audits and the required authorization boundary. "
            "It does not transmit payloads or import external reviews."
        ),
        "no_api": True,
        "broad_api": False,
        "checklist_md": checklist_md,
        "audit_payloads": audit_payloads,
        "payload_files_exist": {name: _repo_path(item["payload_md"]).exists() for name, item in audit_payloads.items()},
        "requires_user_confirmation_before_transmission": True,
        "external_transmission_allowed_now": False,
        "transmission_performed": False,
        "confirmation_boundary": [
            "A future turn must explicitly authorize sending these payload files to an external reviewer/backend.",
            "Authorization to continue local work is not authorization to transmit unpublished manuscript or result payloads.",
            "After review, imported outputs must be saved to the expected_review_md paths and audited before claims are authorized.",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R465_local_smoke_after_source_and_audit_checklists",
    }
    _write_text(checklist_md, render_checklist(summary))
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write external audit authorization checklist.")
    parser.add_argument("--checklist_md", default=DEFAULT_CHECKLIST_MD)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_checklist(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
