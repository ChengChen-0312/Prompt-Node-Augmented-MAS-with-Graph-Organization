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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r442_local_smoke_test_suite_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r442_local_smoke_test_suite_report.md"

SMOKE_TEST_MODULES = [
    "tests.test_r431_draft_claim_sanity_check",
    "tests.test_r432_paper_main_tex_scaffold",
    "tests.test_r433_front_matter_and_related_work_preflight",
    "tests.test_r434_front_matter_initial_draft",
    "tests.test_r435_related_work_bibtex_audit_preflight",
    "tests.test_r436_citation_metadata_fetch_and_bib_skeleton",
    "tests.test_r437_related_work_initial_draft",
    "tests.test_r438_citation_context_static_audit",
    "tests.test_r439_paper_static_integrity_precompile_audit",
    "tests.test_r440_paper_claim_number_static_audit",
    "tests.test_r441_external_audit_package_refresh",
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


def _run_module(module: str) -> Dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", module],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
        check=False,
    )
    return {
        "module": module,
        "returncode": proc.returncode,
        "passed": proc.returncode == 0,
        "output_tail": proc.stdout[-2000:],
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R442 Local Smoke Test Suite",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Local smoke pass: `{summary['local_smoke_pass']}`",
        f"- Tested modules: `{summary['tested_module_count']}`",
        "",
        "## Failed Modules",
        "",
    ]
    if summary["failed_modules"]:
        rows.extend(f"- `{module}`" for module in summary["failed_modules"])
    else:
        rows.append("- none")
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_smoke_suite(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    results = [_run_module(module) for module in SMOKE_TEST_MODULES]
    failed = [row["module"] for row in results if not row["passed"]]
    summary: Dict[str, Any] = {
        "run_id": "R442",
        "title": "Local smoke test suite",
        "claim_boundary": (
            "R442 verifies recent local scripts and tests only. It does not execute external audits "
            "or authorize submission claims."
        ),
        "no_api": True,
        "broad_api": False,
        "tested_module_count": len(SMOKE_TEST_MODULES),
        "test_results": results,
        "failed_modules": failed,
        "local_smoke_pass": not failed,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R443_manuscript_status_snapshot",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run recent R431-R441 smoke tests.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_smoke_suite(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
