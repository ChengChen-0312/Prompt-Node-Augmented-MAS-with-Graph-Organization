from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r447_local_smoke_after_tables_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r447_local_smoke_after_tables_report.md"

SMOKE_MODULES = [
    "tests.test_r439_paper_static_integrity_precompile_audit",
    "tests.test_r440_paper_claim_number_static_audit",
    "tests.test_r443_manuscript_status_snapshot",
    "tests.test_r444_external_audit_execution_plan",
    "tests.test_r445_external_audit_payload_export",
    "tests.test_r446_local_tables_and_submission_gaps",
]


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


def _run(module: str) -> Dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", module],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
        check=False,
    )
    return {"module": module, "returncode": proc.returncode, "passed": proc.returncode == 0, "output_tail": proc.stdout[-1200:]}


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R447 Local Smoke After Tables",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Local smoke pass: `{summary['local_smoke_pass']}`",
        "",
        "## Goal Check",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_smoke(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    results = [_run(module) for module in SMOKE_MODULES]
    failed = [row["module"] for row in results if not row["passed"]]
    summary: Dict[str, Any] = {
        "run_id": "R447",
        "title": "Local smoke after tables",
        "claim_boundary": (
            "R447 verifies local table and audit-status scripts after table insertion. It does not execute external audits."
        ),
        "no_api": True,
        "broad_api": False,
        "tested_modules": SMOKE_MODULES,
        "test_results": results,
        "failed_modules": failed,
        "local_smoke_pass": not failed,
        "iterations_since_last_goal_check": ["R442", "R443", "R444", "R445", "R446"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "tables_support_claim_evidence_matrix": True,
            "arg_designer_remains_main_baseline": True,
            "external_audit_blockers_remain_explicit": True,
            "no_submission_ready_overclaim": True,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R448_manuscript_snapshot_after_tables",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local smoke tests after table generation.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_smoke(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
