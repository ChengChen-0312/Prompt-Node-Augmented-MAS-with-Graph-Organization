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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r448_manuscript_snapshot_after_tables_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r448_manuscript_snapshot_after_tables_report.md"


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
        "# R448 Manuscript Snapshot After Tables",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Tables integrated: `{summary['tables_integrated']}`",
        f"- Local smoke after tables pass: `{summary['local_smoke_after_tables_pass']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        "",
        "## Remaining Gaps",
        "",
    ]
    rows.extend(f"- `{gap}`" for gap in summary["remaining_gaps"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_snapshot(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    r446 = _load_json("experiment/mmlu/res_logs/mmlu_r446_local_tables_and_submission_gaps_summary.json")
    r447 = _load_json("experiment/mmlu/res_logs/mmlu_r447_local_smoke_after_tables_summary.json")
    table_files = r446.get("tables_created", [])
    results_text = _repo_path("paper/sections/5_results.tex").read_text(encoding="utf-8")
    tables_integrated = all(_repo_path(path).exists() for path in table_files) and r"\input{tables/main_results}" in results_text
    summary: Dict[str, Any] = {
        "run_id": "R448",
        "title": "Manuscript snapshot after tables",
        "claim_boundary": (
            "R448 records the table-integrated draft state. It does not execute external audits or compile PDF."
        ),
        "no_api": True,
        "broad_api": False,
        "table_files": table_files,
        "tables_integrated": tables_integrated,
        "local_smoke_after_tables_pass": bool(r447.get("local_smoke_pass")),
        "remaining_gaps": [
            "external_audits_pending",
            "latex_compile_pending",
            "journal_formatting_pending",
            "final_caption_polish_pending",
        ],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R449_next_local_improvement_or_external_audit",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Snapshot manuscript state after table generation.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_snapshot(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
