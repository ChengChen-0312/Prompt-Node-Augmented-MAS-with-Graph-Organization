from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r455_full_local_smoke_after_appendix_artifact_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r455_full_local_smoke_after_appendix_artifact_report.md"

TESTED_MODULES = [
    "tests.test_r449_next_local_improvement_or_external_audit",
    "tests.test_r450_submission_gap_backlog",
    "tests.test_r451_journal_scope_gap_matrix",
    "tests.test_r452_five_run_goal_audit_and_compile_probe",
    "tests.test_r453_appendix_noise_audit_pack",
    "tests.test_r454_reproducibility_artifact_index",
]

SECRET_PATTERNS = {
    "openai_key_value": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "openai_key_assignment": re.compile(r"\bOPENAI_API_KEY\s*=\s*['\"]?[A-Za-z0-9_-]{20,}"),
    "anthropic_key_assignment": re.compile(r"\bANTHROPIC_API_KEY\s*=\s*['\"]?[A-Za-z0-9_-]{20,}"),
    "azure_openai_key_assignment": re.compile(r"\bAZURE_OPENAI_API_KEY\s*=\s*['\"]?[A-Za-z0-9_-]{20,}"),
}


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


def _iter_text_files(paths: Iterable[str]) -> Iterable[Path]:
    for raw in paths:
        root = _repo_path(raw)
        if not root.exists():
            continue
        if root.is_file():
            yield root
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".tex", ".md", ".json", ".bib"}:
                yield path


def _secret_scan(paths: Iterable[str]) -> List[Dict[str, str]]:
    hits: List[Dict[str, str]] = []
    for path in _iter_text_files(paths):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, regex in SECRET_PATTERNS.items():
            if regex.search(text):
                hits.append({"path": str(path.relative_to(REPO_ROOT)), "pattern": name})
    return hits


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R455 Full Local Smoke After Appendix Artifact",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Local smoke pass: `{summary['local_smoke_pass']}`",
        f"- Secret scan pass: `{summary['secret_scan_pass']}`",
        f"- Tested modules: `{len(summary['tested_modules'])}`",
        "",
        "## Failed Modules",
        "",
    ]
    rows.extend(f"- `{module}`" for module in summary["failed_modules"]) if summary["failed_modules"] else rows.append("- none")
    rows.extend(["", "## Secret Scan Hits", ""])
    if summary["secret_scan_hits"]:
        rows.extend(f"- `{hit['path']}` pattern=`{hit['pattern']}`" for hit in summary["secret_scan_hits"])
    else:
        rows.append("- none")
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
    scan_paths = [
        "paper",
        "experiment/mmlu/res_logs",
        "experiment/mmlu/run_logs",
    ]
    secret_hits = _secret_scan(scan_paths)
    summary: Dict[str, Any] = {
        "run_id": "R455",
        "title": "Full local smoke after appendix and artifact index",
        "claim_boundary": (
            "R455 runs recent local tests and a lightweight secret-pattern scan. "
            "It does not execute API calls, external audits, or PDF compilation."
        ),
        "no_api": True,
        "broad_api": False,
        "tested_modules": TESTED_MODULES,
        "test_results": test_results,
        "failed_modules": failed_modules,
        "local_smoke_pass": not failed_modules,
        "secret_scan_paths": scan_paths,
        "secret_scan_patterns": list(SECRET_PATTERNS.keys()),
        "secret_scan_hits": secret_hits,
        "secret_scan_pass": not secret_hits,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R456_next_goal_audit_or_external_review_decision",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run recent local smoke tests and secret-pattern scan.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_smoke(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
