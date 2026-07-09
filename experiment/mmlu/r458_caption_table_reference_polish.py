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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r458_caption_table_reference_polish_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r458_caption_table_reference_polish_report.md"

MAIN_CAPTION = (
    r"\caption{Main split-scoped results. Rows are evidence for the stated slices, not universal benchmark "
    r"claims. Fix/harm/wrong-forward is reported where available; a dash denotes an audit-clean aggregate "
    r"without per-item switch accounting in the table source.}"
)
COST_CAPTION = (
    r"\caption{Cost evidence rows. Direct or existing-summary costs are separated from the MMLU STEM probe "
    r"estimate, which is not exact original R306 accounting.}"
)
RESULT_REFERENCE_BLOCK = (
    r"Table~\ref{tab:main-results} reports split-scoped accuracy evidence rather than universal benchmark "
    r"claims. Table~\ref{tab:cost-results} records cost provenance and separates direct or existing-summary "
    r"costs from probe estimates."
)


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


def _replace_caption(path: str, new_caption: str) -> bool:
    target = _repo_path(path)
    text = target.read_text(encoding="utf-8")
    if new_caption in text:
        return False
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith(r"\caption{"):
            lines[idx] = new_caption
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
    raise ValueError(f"No caption line found in {path}")


def _ensure_result_reference_block() -> bool:
    target = _repo_path("paper/sections/5_results.tex")
    text = target.read_text(encoding="utf-8")
    if RESULT_REFERENCE_BLOCK in text:
        return False
    marker = "\\input{tables/cost_results}\n\n"
    if marker not in text:
        raise ValueError("Could not locate table input marker in results section")
    text = text.replace(marker, marker + RESULT_REFERENCE_BLOCK + "\n\n", 1)
    target.write_text(text, encoding="utf-8")
    return True


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R458 Caption Table Reference Polish",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Main caption changed: `{summary['main_caption_changed']}`",
            f"- Cost caption changed: `{summary['cost_caption_changed']}`",
            f"- Result reference block inserted: `{summary['result_reference_inserted']}`",
            "",
            f"- Paper claim authorized: `{summary['paper_claim_authorized']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run_polish(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "run_id": "R458",
        "title": "Caption table reference polish",
        "claim_boundary": (
            "R458 tightens table captions and cross-references to reduce overclaim risk. "
            "It does not change result values or authorize paper claims."
        ),
        "no_api": True,
        "broad_api": False,
        "main_caption_changed": _replace_caption("paper/tables/main_results.tex", MAIN_CAPTION),
        "cost_caption_changed": _replace_caption("paper/tables/cost_results.tex", COST_CAPTION),
        "result_reference_inserted": _ensure_result_reference_block(),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R459_updated_full_local_smoke_after_polish",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Polish table captions and result references.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_polish(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
