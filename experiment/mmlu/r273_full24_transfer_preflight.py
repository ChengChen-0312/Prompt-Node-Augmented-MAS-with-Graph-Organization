from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r231_tiny_diagnostic_runner import DEFAULT_MODEL, load_jsonl
from experiment.mmlu.r252_mmlu_transfer_preflight import (
    ALL_VARIANTS,
    build_source_lookup,
    build_variant_manifest_rows,
    render_report as render_r252_report,
    summarize_preflight_records,
)


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_r273_records(
    probe_rows: List[Dict[str, Any]],
    source_rows: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 64,
) -> List[Dict[str, Any]]:
    records = build_variant_manifest_rows(
        probe_rows,
        build_source_lookup(source_rows),
        model=model,
        max_completion_tokens=max_completion_tokens,
    )
    for row in records:
        row["run_id"] = "R273"
        row["router_final_schema"]["schema_version"] = "r273_mmlu_full24_transfer_preflight_v1"
        row["router_final_schema"]["scope"] = "MMLU full24 transfer diagnostic"
    return records


def summarize_r273(records: List[Dict[str, Any]], cost_cap: float) -> Dict[str, Any]:
    summary = summarize_preflight_records(records, cost_cap=cost_cap)
    task_roles: Dict[str, str] = {}
    for row in records:
        task_roles[str(row.get("task_id"))] = str(row.get("selection_role"))
    summary.update(
        {
            "run_id": "R273",
            "title": "MMLU full24 transfer preflight",
            "claim_boundary": "Preflight only; no API execution, no transfer accuracy claim, and no SCI-Q2 readiness claim.",
            "selection_role_counts": dict(sorted(Counter(task_roles.values()).items())),
            "balanced_error_control": set(task_roles.values()) == {"arg_error", "matched_control"},
            "authorized_api_next": bool(summary["preflight_pass"]),
        }
    )
    return summary


def run(
    probe_jsonl: str = "experiment/mmlu/run_logs/mmlu_r251_mmlu_transfer_probe_full24.jsonl",
    transfer_results_jsonl: str = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl",
    output_dir: str = "experiment/mmlu/manifests/r273_mmlu_transfer_full24",
    dryrun_jsonl: str = "experiment/mmlu/run_logs/mmlu_r273_full24_transfer_preflight_records.jsonl",
    summary_json: str = "experiment/mmlu/res_logs/mmlu_r273_full24_transfer_preflight_summary.json",
    report_md: str = "experiment/mmlu/run_logs/mmlu_r273_full24_transfer_preflight.md",
    model: str = DEFAULT_MODEL,
    cost_cap: float = 0.25,
    max_completion_tokens: int = 64,
) -> Dict[str, Any]:
    records = build_r273_records(
        load_jsonl(probe_jsonl),
        load_jsonl(transfer_results_jsonl),
        model=model,
        max_completion_tokens=max_completion_tokens,
    )
    os.makedirs(output_dir, exist_ok=True)
    _write_jsonl(os.path.join(output_dir, "mmlu_r273_transfer_manifest_all.jsonl"), records)
    for variant in ALL_VARIANTS:
        _write_jsonl(
            os.path.join(output_dir, f"mmlu_r273_{variant}.jsonl"),
            [row for row in records if row.get("control_variant") == variant],
        )
    _write_jsonl(dryrun_jsonl, records)

    summary = summarize_r273(records, cost_cap=cost_cap)
    summary.update(
        {
            "no_api": True,
            "broad_api": False,
            "model": model,
            "probe_jsonl": probe_jsonl,
            "transfer_results_jsonl": transfer_results_jsonl,
            "output_dir": output_dir,
            "dryrun_jsonl": dryrun_jsonl,
            "max_completion_tokens": max_completion_tokens,
        }
    )
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        report = render_r252_report({**summary, "run_id": "R273"}).replace(
            "# R252 MMLU Transfer Diagnostic Preflight",
            "# R273 MMLU Full24 Transfer Preflight",
        )
        f.write(report)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R273 MMLU full24 transfer preflight manifests.")
    parser.add_argument("--probe_jsonl", default="experiment/mmlu/run_logs/mmlu_r251_mmlu_transfer_probe_full24.jsonl")
    parser.add_argument("--transfer_results_jsonl", default="experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl")
    parser.add_argument("--output_dir", default="experiment/mmlu/manifests/r273_mmlu_transfer_full24")
    parser.add_argument("--dryrun_jsonl", default="experiment/mmlu/run_logs/mmlu_r273_full24_transfer_preflight_records.jsonl")
    parser.add_argument("--summary_json", default="experiment/mmlu/res_logs/mmlu_r273_full24_transfer_preflight_summary.json")
    parser.add_argument("--report_md", default="experiment/mmlu/run_logs/mmlu_r273_full24_transfer_preflight.md")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--cost_cap", type=float, default=0.25)
    parser.add_argument("--max_completion_tokens", type=int, default=64)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
