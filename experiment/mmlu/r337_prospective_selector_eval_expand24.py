from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r335_prospective_selector_eval_api_smoke import (
    DEFAULT_ENV_FILE,
    DEFAULT_MANIFEST_JSONL,
    build_api_smoke_plan,
    execute_api_smoke,
    render_report,
)
from experiment.mmlu.r336_prospective_selector_eval_smoke_analysis import build_smoke_analysis


DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r337_prospective_selector_eval_expand24_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r337_prospective_selector_eval_expand24_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r337_prospective_selector_eval_expand24_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _as_r337(summary: Dict[str, Any], executed: bool) -> Dict[str, Any]:
    out = dict(summary)
    out.update(
        {
            "run_id": "R337",
            "title": "Prospective selector eval expand24",
            "claim_boundary": (
                "R337 expands the R335 smoke to 24 held-out tasks. It remains a bounded prospective diagnostic, not "
                "a final paper claim."
            ),
            "source_smoke_no_harm": True,
            "api_executed": bool(summary.get("api_executed")) if executed else False,
            "next_required_run": "R338_goal_audit_after_prospective_eval" if executed else "R337_execute_with_api_or_R338_goal_audit",
        }
    )
    return out


def build_expand24_plan(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    smoke = build_smoke_analysis()
    plan = build_api_smoke_plan(manifest_jsonl=manifest_jsonl, limit_tasks=24)
    summary = _as_r337(plan, executed=False)
    summary["source_smoke_no_harm"] = bool(smoke.get("claim_permissions", {}).get("selector_no_harm_smoke_allowed"))
    return summary


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    execute_api: bool = False,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    if execute_api:
        records, raw_summary = asyncio.run(execute_api_smoke(manifest_jsonl=manifest_jsonl, env_file=env_file, limit_tasks=24))
        summary = _as_r337(raw_summary, executed=True)
        _write_jsonl(output_jsonl, records)
    else:
        summary = build_expand24_plan(manifest_jsonl=manifest_jsonl)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R337 prospective selector expand24.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--execute_api", action="store_true")
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
