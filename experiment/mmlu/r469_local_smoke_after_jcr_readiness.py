from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r469_local_smoke_after_jcr_readiness_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r469_local_smoke_after_jcr_readiness_report.md"

TESTED_MODULES = [
    "tests.test_r467_jcr_quartile_verification_plan",
    "tests.test_r468_submission_readiness_matrix",
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
        "# R469 Local Smoke After JCR Readiness",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Local smoke pass: `{summary['local_smoke_pass']}`",
        f"- Tested modules: `{len(summary['tested_modules'])}`",
        "",
        "## Failed Modules",
        "",
    ]
    rows.extend(f"- `{module}`" for module in summary["failed_modules"]) if summary["failed_modules"] else rows.append("- none")
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


def run_smoke(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    test_results = [_run_module(module) for module in TESTED_MODULES]
    failed_modules = [row["module"] for row in test_results if not row["passed"]]
    summary: Dict[str, Any] = {
        "run_id": "R469",
        "title": "Local smoke after JCR readiness artifacts",
        "claim_boundary": (
            "R469 runs local tests for JCR verification planning and submission readiness matrix. "
            "It does not verify official JCR status or execute blocked steps."
        ),
        "no_api": True,
        "broad_api": False,
        "tested_modules": TESTED_MODULES,
        "test_results": test_results,
        "failed_modules": failed_modules,
        "local_smoke_pass": not failed_modules,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R470_current_status_digest",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local smoke tests for JCR/readiness artifacts.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_smoke(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
