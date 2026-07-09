from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import (
    DEFAULT_MMLU_TEST_DIR,
    EXCLUDED_JSONL_PATHS,
    NONSTEM_SUBJECTS,
    STEM_SUBJECTS,
    _api_record,
    _leakage,
    _load_subject_records,
    _used_task_ids,
)
from experiment.mmlu.r352_fresh_coverage_promptnode_expansion_preflight import run_expanded_promptnodes
from experiment.mmlu.r346_tool_backed_promptnode_local_preflight import _label


DEFAULT_API_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r354_fresh_eval_after_coverage_expansion_api_manifest.jsonl"
DEFAULT_LOCAL_TOOL_JSONL = "experiment/mmlu/run_logs/mmlu_r354_fresh_eval_after_coverage_expansion_local_tool_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r354_fresh_eval_after_coverage_expansion_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r354_fresh_eval_after_coverage_expansion_preflight_report.md"
EXTRA_EXCLUDED_JSONL_PATHS = [
    "experiment/mmlu/run_logs/mmlu_r352_fresh_coverage_promptnode_expansion_preflight_results.jsonl",
]


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


def _local_tool_record(task: Dict[str, Any]) -> Dict[str, Any]:
    result = run_expanded_promptnodes(task["question"])
    candidate = _label(result.get("candidate_label"))
    true_answer = _label(task.get("evaluation_only", {}).get("true_answer"))
    return {
        "run_id": "R354",
        "task_id": task["task_id"],
        "dataset_family": task["dataset_family"],
        "subject": task["subject"],
        "row_index": task["row_index"],
        "control_variant": "expanded_tool_promptnode_local",
        "candidate_label": candidate,
        "promptnode_id": result.get("promptnode_id"),
        "promptedge_contract_pass": bool(result.get("promptedge_contract_pass")),
        "candidate_is_correct": candidate == true_answer if candidate else False,
        "evaluation_only": task["evaluation_only"],
        "evidence": result.get("evidence"),
    }


def build_fresh_preflight(mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    used = _used_task_ids(EXCLUDED_JSONL_PATHS + EXTRA_EXCLUDED_JSONL_PATHS)
    stem = _load_subject_records(mmlu_test_dir, STEM_SUBJECTS, "mmlu_stem", 4, used)[:24]
    nonstem = _load_subject_records(mmlu_test_dir, NONSTEM_SUBJECTS, "mmlu_nonstem", 3, used)[:24]
    tasks = stem + nonstem
    api_records = [_api_record(task) | {"run_id": "R354"} for task in tasks]
    local_records = [_local_tool_record(task) for task in tasks]
    violations = _leakage(api_records)
    task_ids = {task["task_id"] for task in tasks}
    overlap = task_ids & used
    family_counts = Counter(task["dataset_family"] for task in tasks)
    forwarded = [row for row in local_records if row.get("candidate_label")]
    summary = {
        "run_id": "R354",
        "title": "Fresh eval after coverage expansion preflight",
        "claim_boundary": (
            "R354 builds a new fresh split after R352 coverage expansion. The expanded local policy still forwards "
            "zero candidates, so API execution is blocked to avoid a no-op comparison."
        ),
        "no_api": True,
        "broad_api": False,
        "policy_frozen_after_run": "R352",
        "tasks": len(tasks),
        "task_family_counts": dict(sorted(family_counts.items())),
        "api_manifest_records": len(api_records),
        "local_tool_records": len(local_records),
        "api_calls_planned": sum(1 for row in api_records if row.get("api_required")),
        "local_tool_forwarded_candidate_count": len(forwarded),
        "local_tool_candidate_correct_count": sum(1 for row in forwarded if row.get("candidate_is_correct")),
        "overlap_with_excluded_task_count": len(overlap),
        "overlap_with_excluded_task_ids": sorted(overlap),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_execution_authorized_next": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R355_goal_audit_after_second_fresh_preflight",
    }
    return api_records, local_records, summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R354 Fresh Eval After Coverage Expansion Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- Family counts: `{summary['task_family_counts']}`",
            f"- Local tool forwarded candidates: `{summary['local_tool_forwarded_candidate_count']}`",
            f"- API execution authorized next: `{summary['api_execution_authorized_next']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR,
    api_manifest_jsonl: str = DEFAULT_API_MANIFEST_JSONL,
    local_tool_jsonl: str = DEFAULT_LOCAL_TOOL_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    api_records, local_records, summary = build_fresh_preflight(mmlu_test_dir=mmlu_test_dir)
    summary.update(
        {
            "api_manifest_jsonl": api_manifest_jsonl,
            "local_tool_jsonl": local_tool_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    _write_jsonl(api_manifest_jsonl, api_records)
    _write_jsonl(local_tool_jsonl, local_records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R354 fresh eval preflight after coverage expansion.")
    parser.add_argument("--mmlu_test_dir", default=DEFAULT_MMLU_TEST_DIR)
    parser.add_argument("--api_manifest_jsonl", default=DEFAULT_API_MANIFEST_JSONL)
    parser.add_argument("--local_tool_jsonl", default=DEFAULT_LOCAL_TOOL_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
