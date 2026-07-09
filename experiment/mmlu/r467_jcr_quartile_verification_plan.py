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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r467_jcr_quartile_verification_plan_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r467_jcr_quartile_verification_plan_report.md"
DEFAULT_PLAN_MD = "paper/artifacts/jcr_quartile_verification_plan.md"


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


def render_plan(summary: Dict[str, Any]) -> str:
    rows = [
        "# JCR Quartile Verification Plan",
        "",
        "Public metric pages are only planning evidence. Final SCI quartile status must be checked in official JCR or institutional Web of Science access immediately before submission.",
        "",
        "## Target Journals",
        "",
    ]
    for journal in summary["target_journals"]:
        rows.append(f"- `{journal}`")
    rows.extend(["", "## Public Metric Sources", ""])
    for item in summary["public_metric_sources"]:
        rows.append(f"- `{item['journal']}`: {item['source_url']} ({item['planning_evidence']})")
    rows.extend(["", "## Official Verification Steps", ""])
    rows.extend(f"- {step}" for step in summary["official_verification_steps"])
    rows.append("")
    return "\n".join(rows)


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R467 JCR Quartile Verification Plan",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Plan: `{summary['plan_md']}`",
        f"- Official JCR verification completed: `{summary['official_jcr_verification_completed']}`",
        "",
        f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run_plan(
    plan_md: str = DEFAULT_PLAN_MD,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "run_id": "R467",
        "title": "JCR quartile verification plan",
        "claim_boundary": (
            "R467 records public planning evidence and the official quartile-verification procedure. "
            "It does not claim official JCR verification or certify SCI-Q2 readiness."
        ),
        "no_api": True,
        "broad_api": False,
        "plan_md": plan_md,
        "target_journals": ["JAIR", "KAIS"],
        "public_metric_sources": [
            {
                "journal": "JAIR",
                "source_url": "https://www.journalmetrics.org/journal/journal-of-artificial-intelligence-research",
                "planning_evidence": "Public page reports JCR Q2 in the current planning snapshot.",
            },
            {
                "journal": "KAIS",
                "source_url": "https://www.journalmetrics.org/journal/knowledge-and-information-systems",
                "planning_evidence": "Public page reports JCR Q2 in the current planning snapshot.",
            },
        ],
        "source_caveat": (
            "Public metric pages are not authoritative for submission decisions; final status must be verified in official JCR "
            "or institutional Web of Science access near submission time."
        ),
        "official_verification_steps": [
            "Open official Journal Citation Reports through institutional Web of Science access.",
            "Search the full journal title and ISSN for JAIR and KAIS.",
            "Record year, category, JIF quartile, ESCI/SCIE indexing, and screenshot or exported metadata location.",
            "Only after this step may the manuscript package call a target venue SCI-Q2-verified.",
        ],
        "official_jcr_verification_completed": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R468_submission_readiness_matrix",
    }
    _write_text(plan_md, render_plan(summary))
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write JCR quartile verification plan.")
    parser.add_argument("--plan_md", default=DEFAULT_PLAN_MD)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_plan(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
