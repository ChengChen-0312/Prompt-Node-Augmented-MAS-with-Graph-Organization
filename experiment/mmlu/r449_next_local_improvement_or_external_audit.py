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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r449_next_local_improvement_or_external_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r449_next_local_improvement_or_external_audit_report.md"


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


def _recommended_q2_targets() -> List[Dict[str, str]]:
    return [
        {
            "short_name": "JAIR",
            "journal": "Journal of Artificial Intelligence Research",
            "fit": "best_scope_fit_for_agents_and_mas",
            "q_evidence": "JournalMetrics 2026 page reports JCR Q2; verify in official JCR before submission.",
            "scope_evidence": "Official JAIR scope lists agents and multi-agent systems.",
            "risk": "High quality bar; needs external audits, stronger framing, and polished case evidence.",
        },
        {
            "short_name": "KAIS",
            "journal": "Knowledge and Information Systems",
            "fit": "backup_fit_for_ai_knowledge_systems_and_evaluation",
            "q_evidence": "JournalMetrics 2026 page reports JCR Q2; verify in official JCR before submission.",
            "scope_evidence": "Potentially fits if framed as knowledge-guided MAS graph organization and reliable evaluation.",
            "risk": "May prefer data mining or knowledge-systems framing over pure LLM-agent engineering.",
        },
    ]


def _not_preferred_targets() -> List[Dict[str, str]]:
    return [
        {
            "short_name": "EAAI",
            "journal": "Engineering Applications of Artificial Intelligence",
            "reason": "Strong AI application outlet, but current evidence points to Q1 rather than conservative SCI-Q2 targeting.",
        },
        {
            "short_name": "ASOC",
            "journal": "Applied Soft Computing",
            "reason": "Strong related outlet, but current evidence points to Q1 rather than conservative SCI-Q2 targeting.",
        },
        {
            "short_name": "IJMLC",
            "journal": "International Journal of Machine Learning and Cybernetics",
            "reason": "Scope may fit, but current public ranking evidence is ambiguous or Q3; not a primary SCI-Q2 target yet.",
        },
    ]


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R449 Next Local Improvement Or External Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Recommended SCI-Q2 Targets",
        "",
    ]
    for target in summary["recommended_q2_targets"]:
        rows.extend(
            [
                f"### {target['short_name']}: {target['journal']}",
                "",
                f"- Fit: `{target['fit']}`",
                f"- Q evidence: {target['q_evidence']}",
                f"- Scope evidence: {target['scope_evidence']}",
                f"- Risk: {target['risk']}",
                "",
            ]
        )
    rows.extend(["## Not Preferred Now", ""])
    for target in summary["not_preferred_targets"]:
        rows.append(f"- `{target['short_name']}` ({target['journal']}): {target['reason']}")
    rows.extend(["", "## Next Priority Order", ""])
    rows.extend(f"{idx}. `{item}`" for idx, item in enumerate(summary["next_priority_order"], start=1))
    rows.extend(
        [
            "",
            "## Sources Used",
            "",
        ]
    )
    rows.extend(f"- {source}" for source in summary["sources_used"])
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


def run_plan(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "run_id": "R449",
        "title": "Next local improvement or external audit",
        "claim_boundary": (
            "R449 records the SCI-Q2 target-journal orientation and next execution priority. "
            "It does not change experimental claims, execute external audits, or certify submission readiness."
        ),
        "no_api": True,
        "broad_api": False,
        "recommended_q2_targets": _recommended_q2_targets(),
        "not_preferred_targets": _not_preferred_targets(),
        "next_priority_order": [
            "external_audits_before_claim_authorization",
            "submission_gap_backlog_and_journal_scope_mapping",
            "journal_template_and_format_probe",
            "caption_and_contribution_polish_after_audit",
            "latex_compile_after_engine_available",
        ],
        "sources_used": [
            "https://www.journalmetrics.org/journal/journal-of-artificial-intelligence-research",
            "https://www.jair.org/",
            "https://www.journalmetrics.org/journal/knowledge-and-information-systems",
            "https://clarivate.com/academia-government/scientific-and-academic-research/research-discovery-and-workflow-solutions/webofscience-platform/science-citation-index-expanded/",
            "https://clarivate.com/academia-government/scientific-and-academic-research/research-discovery-and-workflow-solutions/journal-citation-reports/",
        ],
        "source_caveat": (
            "Public journal-metric pages are planning evidence only; final quartile must be verified in official JCR "
            "or the user's institutional Web of Science access immediately before submission."
        ),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R450_submission_gap_backlog",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record next SCI-Q2-oriented manuscript priority.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_plan(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
