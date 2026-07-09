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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r462_journal_template_probe_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r462_journal_template_probe_report.md"
DEFAULT_TEMPLATE_PLAN_MD = "paper/artifacts/journal_template_probe.md"


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


def _template_sources() -> Dict[str, Dict[str, str]]:
    return {
        "JAIR": {
            "journal": "Journal of Artificial Intelligence Research",
            "template": "JAIR Author Kit / new JAIR LaTeX style, also available through the official Overleaf template.",
            "source_url": "https://www.jair.org/index.php/jair/formatting",
            "submission_url": "https://jair.org/index.php/jair/about/submissions",
            "local_action": "Keep current article scaffold until external audits are resolved; then convert to JAIR Author Kit.",
        },
        "KAIS": {
            "journal": "Knowledge and Information Systems",
            "template": "Springer Nature LaTeX template; submission should include source and compiled PDF.",
            "source_url": "https://link.springer.com/journal/10115/submission-guidelines",
            "template_url": "https://www.springernature.com/gp/authors/campaigns/latex-author-support",
            "local_action": "Use as backup template path if JAIR framing is rejected or scope fit changes.",
        },
    }


def render_template_plan(summary: Dict[str, Any]) -> str:
    rows = [
        "# Journal Template Probe",
        "",
        "This file records the current journal-template decision for the PromptNode-Augmented MAS paper draft.",
        "",
        f"- Primary template target: `{summary['primary_template_target']}`",
        f"- Backup template target: `{summary['backup_template_target']}`",
        f"- Template conversion performed now: `{summary['template_conversion_performed']}`",
        "",
        "## Sources",
        "",
    ]
    for key, item in summary["template_sources"].items():
        rows.extend(
            [
                f"### {key}: {item['journal']}",
                "",
                f"- Template: {item['template']}",
                f"- Source: {item['source_url']}",
                f"- Local action: {item['local_action']}",
                "",
            ]
        )
    rows.extend(["## Conversion Policy", ""])
    rows.extend(f"- {item}" for item in summary["conversion_policy"])
    rows.append("")
    return "\n".join(rows)


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R462 Journal Template Probe",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Primary template target: `{summary['primary_template_target']}`",
        f"- Backup template target: `{summary['backup_template_target']}`",
        f"- Template plan: `{summary['template_plan_md']}`",
        f"- Template conversion performed: `{summary['template_conversion_performed']}`",
        "",
        f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run_probe(
    template_plan_md: str = DEFAULT_TEMPLATE_PLAN_MD,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "run_id": "R462",
        "title": "Journal template probe",
        "claim_boundary": (
            "R462 records official template sources and conversion policy. It does not convert the manuscript, "
            "compile PDF, or certify journal readiness."
        ),
        "no_api": True,
        "broad_api": False,
        "primary_template_target": "JAIR",
        "backup_template_target": "KAIS",
        "template_sources": _template_sources(),
        "template_plan_md": template_plan_md,
        "template_conversion_performed": False,
        "conversion_policy": [
            "Do not convert the full manuscript before external experiment/citation/claim audits are resolved.",
            "Preserve the current article scaffold as the editable working source.",
            "When converting to JAIR, start from the JAIR Author Kit and port sections/tables/appendix with labels preserved.",
            "If switching to KAIS, use Springer Nature article template and keep source plus compiled PDF package.",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R463_source_package_manifest",
    }
    _write_text(template_plan_md, render_template_plan(summary))
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record journal template sources and conversion policy.")
    parser.add_argument("--template_plan_md", default=DEFAULT_TEMPLATE_PLAN_MD)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_probe(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
