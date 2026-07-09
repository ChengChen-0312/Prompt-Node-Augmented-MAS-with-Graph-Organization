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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r444_external_audit_execution_plan_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r444_external_audit_execution_plan_report.md"

EXECUTION_ORDER = ["experiment_integrity_audit", "paper_claim_audit", "citation_context_audit"]


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
        "# R444 External Audit Execution Plan",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Execution Order",
        "",
    ]
    for name in summary["execution_order"]:
        item = summary["audit_execution_plan"][name]
        rows.append(f"- `{name}`: prompt=`{item['prompt_md']}`, output=`{item['expected_output_md']}`")
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_plan(
    r441_summary: str = "experiment/mmlu/res_logs/mmlu_r441_external_audit_package_refresh_summary.json",
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    r441 = _load_json(r441_summary)
    packages = r441.get("audit_packages", {})
    plan = {
        "experiment_integrity_audit": {
            "prompt_md": packages.get("experiment_integrity_audit", {}).get("prompt_md"),
            "files": packages.get("experiment_integrity_audit", {}).get("files", []),
            "expected_output_md": "experiment/mmlu/run_logs/mmlu_r445_experiment_integrity_external_review.md",
            "purpose": "Verify result provenance, scope, and no fake/phantom claim.",
        },
        "paper_claim_audit": {
            "prompt_md": packages.get("paper_claim_audit", {}).get("prompt_md"),
            "files": packages.get("paper_claim_audit", {}).get("files", []),
            "expected_output_md": "experiment/mmlu/run_logs/mmlu_r445_paper_claim_external_review.md",
            "purpose": "Verify every number and comparison against raw/result files.",
        },
        "citation_context_audit": {
            "prompt_md": packages.get("citation_context_audit", {}).get("prompt_md"),
            "files": packages.get("citation_context_audit", {}).get("files", []),
            "expected_output_md": "experiment/mmlu/run_logs/mmlu_r445_citation_context_external_review.md",
            "purpose": "Verify citation existence, metadata, and context support.",
        },
    }
    ready = all(plan[name]["prompt_md"] and _repo_path(plan[name]["prompt_md"]).exists() for name in EXECUTION_ORDER)
    summary: Dict[str, Any] = {
        "run_id": "R444",
        "title": "External audit execution plan",
        "claim_boundary": (
            "R444 orders the external audit execution and output capture paths. "
            "It does not execute external reviews."
        ),
        "no_api": True,
        "broad_api": False,
        "execution_order": EXECUTION_ORDER,
        "audit_execution_plan": plan,
        "external_audit_execution_ready": ready,
        "external_reviews_executed": [],
        "execution_backends_allowed": ["in_app_browser_gpt5_5pro", "api_fresh_reviewer_if_available", "manual_import"],
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R445_external_audit_execution_or_manual_import",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan external audit execution and output capture.")
    parser.add_argument("--r441_summary", default="experiment/mmlu/res_logs/mmlu_r441_external_audit_package_refresh_summary.json")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_plan(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
