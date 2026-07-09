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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r450_submission_gap_backlog_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r450_submission_gap_backlog_report.md"


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


def _make_backlog(r443: Dict[str, Any], r448: Dict[str, Any], r449: Dict[str, Any]) -> List[Dict[str, str]]:
    blockers = set(r443.get("remaining_blockers", [])) | set(r448.get("remaining_gaps", []))
    target_names = ", ".join(target["short_name"] for target in r449.get("recommended_q2_targets", []))
    return [
        {
            "id": "B450-001",
            "priority": "P0",
            "item": "external experiment-integrity audit pending",
            "evidence": "R443/R444/R445 prepared audit packages but no independent review has been executed.",
            "required_action": "Run or import a fresh external review of result provenance before authorizing claims.",
            "next_run": "R451_or_external_review_import",
            "status": "open" if "external_experiment_integrity_audit_pending" in blockers else "unknown",
        },
        {
            "id": "B450-002",
            "priority": "P0",
            "item": "external paper-claim audit pending",
            "evidence": "R440 is only a static local number audit; zero-context claim audit remains pending.",
            "required_action": "Check every manuscript number and comparison against raw/result files using a fresh reviewer.",
            "next_run": "R451_or_external_review_import",
            "status": "open",
        },
        {
            "id": "B450-003",
            "priority": "P0",
            "item": "external citation-context audit pending",
            "evidence": "R436/R438 built citation metadata and contexts, but no external citation audit is recorded.",
            "required_action": "Verify that each cited paper exists and each citation context is supported.",
            "next_run": "R451_or_external_review_import",
            "status": "open",
        },
        {
            "id": "B450-004",
            "priority": "P1",
            "item": "journal scope matrix missing",
            "evidence": f"R449 selected target journals ({target_names}) but did not map claims to their scopes.",
            "required_action": "Build a JAIR/KAIS scope-gap matrix and decide the primary framing.",
            "next_run": "R451_journal_scope_gap_matrix",
            "status": "open",
        },
        {
            "id": "B450-005",
            "priority": "P1",
            "item": "latex compile unavailable",
            "evidence": "R439 found no local latexmk or pdflatex, so PDF compile has not been verified.",
            "required_action": "Install or locate a TeX engine, then compile and inspect the PDF.",
            "next_run": "R452_compile_probe_or_environment_note",
            "status": "open" if "latex_compile_pending" in blockers else "unknown",
        },
        {
            "id": "B450-006",
            "priority": "P1",
            "item": "audit-clean appendix needs finalization",
            "evidence": "AQuA and MMLU label-noise decisions are recorded in result logs, but the appendix needs final wording.",
            "required_action": "Finalize appendix language for task_59/task_139/task_228/task_114 and MMLU audited items.",
            "next_run": "R453_appendix_noise_audit_pack",
            "status": "open",
        },
        {
            "id": "B450-007",
            "priority": "P2",
            "item": "caption and contribution polish pending",
            "evidence": "R448 records final caption polish as pending after table integration.",
            "required_action": "Polish captions only after external audits decide which claims survive.",
            "next_run": "R454_caption_polish_after_audit",
            "status": "blocked_by_external_audits",
        },
        {
            "id": "B450-008",
            "priority": "P2",
            "item": "reproducibility artifact packaging pending",
            "evidence": "Experiment code and ledgers exist, but a reader-facing reproduction README is not yet packaged.",
            "required_action": "Prepare a concise artifact checklist with commands, splits, costs, and audit-clean protocol.",
            "next_run": "R455_reproducibility_artifact_index",
            "status": "open",
        },
    ]


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R450 Submission Gap Backlog",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Target journals: `{', '.join(summary['target_journals'])}`",
        f"- External transmission allowed now: `{summary['external_transmission_allowed_now']}`",
        f"- Requires user confirmation for external transmission: `{summary['requires_user_confirmation_for_external_transmission']}`",
        "",
        "## Backlog",
        "",
    ]
    for item in summary["backlog_items"]:
        rows.extend(
            [
                f"### {item['id']} ({item['priority']}): {item['item']}",
                "",
                f"- Evidence: {item['evidence']}",
                f"- Required action: {item['required_action']}",
                f"- Next run: `{item['next_run']}`",
                f"- Status: `{item['status']}`",
                "",
            ]
        )
    rows.extend(
        [
            f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )
    return "\n".join(rows)


def run_backlog(
    r443_summary: str = "experiment/mmlu/res_logs/mmlu_r443_manuscript_status_snapshot_summary.json",
    r448_summary: str = "experiment/mmlu/res_logs/mmlu_r448_manuscript_snapshot_after_tables_summary.json",
    r449_summary: str = "experiment/mmlu/res_logs/mmlu_r449_next_local_improvement_or_external_audit_summary.json",
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    r443 = _load_json(r443_summary)
    r448 = _load_json(r448_summary)
    r449 = _load_json(r449_summary)
    target_journals = [target["short_name"] for target in r449.get("recommended_q2_targets", [])]
    summary: Dict[str, Any] = {
        "run_id": "R450",
        "title": "Submission gap backlog",
        "claim_boundary": (
            "R450 converts the current manuscript blockers into an execution backlog. "
            "It does not transmit unpublished material, execute external audits, or certify SCI-Q2 readiness."
        ),
        "no_api": True,
        "broad_api": False,
        "target_journals": target_journals,
        "backlog_items": _make_backlog(r443, r448, r449),
        "external_transmission_allowed_now": False,
        "requires_user_confirmation_for_external_transmission": True,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R451_journal_scope_gap_matrix",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build submission gap backlog.")
    parser.add_argument("--r443_summary", default="experiment/mmlu/res_logs/mmlu_r443_manuscript_status_snapshot_summary.json")
    parser.add_argument("--r448_summary", default="experiment/mmlu/res_logs/mmlu_r448_manuscript_snapshot_after_tables_summary.json")
    parser.add_argument("--r449_summary", default="experiment/mmlu/res_logs/mmlu_r449_next_local_improvement_or_external_audit_summary.json")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_backlog(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
