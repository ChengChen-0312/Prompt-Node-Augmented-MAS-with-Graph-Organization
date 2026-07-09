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


DEFAULT_R428 = "experiment/mmlu/res_logs/mmlu_r428_updated_local_claim_integrity_precheck_summary.json"
DEFAULT_R420 = "experiment/mmlu/res_logs/mmlu_r420_paper_asset_table_refresh_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r429_paper_method_results_draft_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r429_paper_method_results_draft_preflight_report.md"


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


def build_draft_preflight(r428_summary: str = DEFAULT_R428, r420_summary: str = DEFAULT_R420) -> Dict[str, Any]:
    r428 = _load_json(r428_summary)
    r420 = _load_json(r420_summary)
    local_pass = all(check.get("status") == "PASS" for check in r428.get("checks", {}).values())
    return {
        "run_id": "R429",
        "title": "Paper method/results draft preflight",
        "claim_boundary": (
            "R429 authorizes drafting bounded method/results prose from locally verified assets. It does not authorize "
            "final claims before external integrity audit."
        ),
        "no_api": True,
        "broad_api": False,
        "paper_draft_authorized_next": bool(local_pass and r428.get("paper_draft_authorized_next")),
        "paper_claim_authorized": False,
        "external_integrity_audit_required": True,
        "draft_sections_allowed": [
            "Method",
            "Experimental Setup",
            "Results",
            "Cost Analysis",
            "Case Studies",
            "Limitations",
        ],
        "draft_sources": {
            "paper_assets": r420.get("paper_assets", []),
            "local_precheck": r428_summary,
        },
        "required_qualifiers": [
            "MMLU STEM cost is probe-estimated, not exact original R306 accounting.",
            "DefinitionChallenge nonmath result is targeted/narrow.",
            "Lifecycle trace is replayed from R413 outputs, not new accuracy evidence.",
            "External experiment integrity audit is pending.",
        ],
        "forbidden_phrases": [
            "broad nonmath improvement",
            "universal multiple-choice improvement",
            "submission-ready",
            "exact MMLU STEM cost",
            "external audit passed",
        ],
        "paper_claim_authorized_reason": "external_integrity_audit_pending",
        "sci_q2_ready": False,
        "next_required_run": "R430_draft_method_results_sections",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R429 Paper Method/Results Draft Preflight",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Draft authorized next: `{summary['paper_draft_authorized_next']}`",
        f"- External integrity audit required: `{summary['external_integrity_audit_required']}`",
        "",
        "## Allowed Sections",
        "",
    ]
    rows.extend(f"- {section}" for section in summary["draft_sections_allowed"])
    rows.extend(["", "## Required Qualifiers", ""])
    rows.extend(f"- {item}" for item in summary["required_qualifiers"])
    rows.extend(["", "## Forbidden Phrases", ""])
    rows.extend(f"- `{item}`" for item in summary["forbidden_phrases"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r428_summary: str = DEFAULT_R428,
    r420_summary: str = DEFAULT_R420,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_draft_preflight(r428_summary=r428_summary, r420_summary=r420_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build paper method/results draft preflight.")
    parser.add_argument("--r428_summary", default=DEFAULT_R428)
    parser.add_argument("--r420_summary", default=DEFAULT_R420)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
