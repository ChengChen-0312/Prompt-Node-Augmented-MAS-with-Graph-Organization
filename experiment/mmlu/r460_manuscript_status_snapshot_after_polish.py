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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r460_manuscript_status_snapshot_after_polish_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r460_manuscript_status_snapshot_after_polish_report.md"


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


def _remaining_blockers(r452: Dict[str, Any]) -> List[str]:
    blockers = [
        "external_experiment_integrity_audit_pending",
        "external_paper_claim_audit_pending",
        "external_citation_context_audit_pending",
        "journal_template_formatting_pending",
    ]
    if not r452.get("latex_engine_available"):
        blockers.append("latex_engine_missing_for_pdf_compile")
    else:
        blockers.append("pdf_compile_pending")
    return blockers


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R460 Manuscript Status Snapshot After Polish",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Appendix integrated: `{summary['appendix_integrated']}`",
        f"- Artifact index exists: `{summary['artifact_index_exists']}`",
        f"- Local smoke after polish pass: `{summary['local_smoke_after_polish_pass']}`",
        "",
        "## Remaining Blockers",
        "",
    ]
    rows.extend(f"- `{blocker}`" for blocker in summary["remaining_blockers"])
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


def run_snapshot(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    r452 = _load_json("experiment/mmlu/res_logs/mmlu_r452_five_run_goal_audit_and_compile_probe_summary.json")
    r457 = _load_json("experiment/mmlu/res_logs/mmlu_r457_static_manuscript_audit_after_appendix_summary.json")
    r459 = _load_json("experiment/mmlu/res_logs/mmlu_r459_updated_full_local_smoke_after_polish_summary.json")
    summary: Dict[str, Any] = {
        "run_id": "R460",
        "title": "Manuscript status snapshot after polish",
        "claim_boundary": (
            "R460 summarizes the local manuscript state after appendix and caption polish. "
            "It does not execute external audits or mark the paper submission-ready."
        ),
        "no_api": True,
        "broad_api": False,
        "paper_files": [
            "paper/main.tex",
            "paper/sections/0_abstract.tex",
            "paper/sections/1_introduction.tex",
            "paper/sections/2_related_work.tex",
            "paper/sections/3_method.tex",
            "paper/sections/4_experimental_setup.tex",
            "paper/sections/5_results.tex",
            "paper/sections/6_case_studies.tex",
            "paper/sections/7_limitations.tex",
            "paper/sections/8_conclusion.tex",
            "paper/appendices/label_audit.tex",
            "paper/tables/main_results.tex",
            "paper/tables/cost_results.tex",
            "paper/artifacts/reproducibility_index.md",
        ],
        "appendix_integrated": bool(r457.get("appendix_integrated")),
        "artifact_index_exists": _repo_path("paper/artifacts/reproducibility_index.md").exists(),
        "local_smoke_after_polish_pass": bool(r459.get("local_smoke_pass")),
        "static_audit_after_appendix_pass": not r457.get("missing_inputs") and not r457.get("todo_hits"),
        "remaining_blockers": _remaining_blockers(r452),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R461_five_run_goal_audit_after_polish",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Snapshot manuscript state after appendix/caption polish.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_snapshot(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
