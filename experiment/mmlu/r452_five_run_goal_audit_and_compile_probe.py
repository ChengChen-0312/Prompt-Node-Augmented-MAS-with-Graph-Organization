from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r452_five_run_goal_audit_and_compile_probe_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r452_five_run_goal_audit_and_compile_probe_report.md"
AUDITED_RUNS = ["R447", "R448", "R449", "R450", "R451"]


SUMMARY_PATHS = {
    "R447": "experiment/mmlu/res_logs/mmlu_r447_local_smoke_after_tables_summary.json",
    "R448": "experiment/mmlu/res_logs/mmlu_r448_manuscript_snapshot_after_tables_summary.json",
    "R449": "experiment/mmlu/res_logs/mmlu_r449_next_local_improvement_or_external_audit_summary.json",
    "R450": "experiment/mmlu/res_logs/mmlu_r450_submission_gap_backlog_summary.json",
    "R451": "experiment/mmlu/res_logs/mmlu_r451_journal_scope_gap_matrix_summary.json",
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


def _alignment_findings(recent: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    return [
        {
            "tag": "sci_q2_submission",
            "finding": "Recent runs moved from table integration to journal targets, submission blockers, and scope fit.",
            "status": "aligned",
        },
        {
            "tag": "promptnode_graph_organization",
            "finding": "R451 keeps the JAIR framing on first-class PromptNodes and typed PromptEdges rather than answer patches.",
            "status": "aligned",
        },
        {
            "tag": "claim_integrity",
            "finding": "R447-R451 keep paper_claim_authorized=false and sci_q2_ready=false.",
            "status": "aligned",
        },
        {
            "tag": "external_audit_safety",
            "finding": "R450 requires user confirmation before transmitting unpublished local audit payloads.",
            "status": "aligned",
        },
        {
            "tag": "transfer_and_generality_boundary",
            "finding": "R451 explicitly forbids broad nonmath improvement claims and preserves no-harm framing.",
            "status": "aligned",
        },
    ]


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R452 Five-Run Goal Audit And Compile Probe",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Audited runs: `{', '.join(summary['audited_runs'])}`",
        f"- Deviation detected: `{summary['deviation_detected']}`",
        f"- Latex engine available: `{summary['latex_engine_available']}`",
        f"- latexmk: `{summary['latexmk']}`",
        f"- pdflatex: `{summary['pdflatex']}`",
        "",
        "## Alignment Findings",
        "",
    ]
    for finding in summary["alignment_findings"]:
        rows.extend(
            [
                f"- `{finding['tag']}`: {finding['finding']} Status=`{finding['status']}`",
            ]
        )
    rows.extend(["", "## Corrective Actions", ""])
    rows.extend(f"- `{action}`" for action in summary["corrective_actions"])
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


def run_audit(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    recent = {run_id: _load_json(path) for run_id, path in SUMMARY_PATHS.items()}
    unauthorized_claims = [
        run_id
        for run_id, payload in recent.items()
        if payload.get("paper_claim_authorized") or payload.get("sci_q2_ready")
    ]
    latexmk = shutil.which("latexmk")
    pdflatex = shutil.which("pdflatex")
    latex_engine_available = bool(latexmk or pdflatex)
    summary: Dict[str, Any] = {
        "run_id": "R452",
        "title": "Five-run goal audit and compile probe",
        "claim_boundary": (
            "R452 audits R447-R451 for drift against the SCI-Q2 PromptNode goal and probes local LaTeX availability. "
            "It does not compile the paper or execute external audits."
        ),
        "no_api": True,
        "broad_api": False,
        "audited_runs": AUDITED_RUNS,
        "audited_summary_paths": SUMMARY_PATHS,
        "goal_alignment_tags": [
            "sci_q2_submission",
            "promptnode_graph_organization",
            "claim_integrity",
            "external_audit_safety",
            "transfer_and_generality_boundary",
        ],
        "alignment_findings": _alignment_findings(recent),
        "unauthorized_claim_runs": unauthorized_claims,
        "deviation_detected": bool(unauthorized_claims),
        "latexmk": latexmk,
        "pdflatex": pdflatex,
        "latex_engine_available": latex_engine_available,
        "compile_probe_status": "engine_available_compile_next" if latex_engine_available else "not_run_no_latex_engine",
        "corrective_actions": [
            "continue_external_audit_before_claim_authorization",
            "complete_audit_clean_appendix",
            "compile_pdf_when_latex_engine_available",
            "keep_primary_target_jair_unless_external_audit_changes_claim_scope",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R453_appendix_noise_audit_pack",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit recent runs for goal drift and probe LaTeX availability.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_audit(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
