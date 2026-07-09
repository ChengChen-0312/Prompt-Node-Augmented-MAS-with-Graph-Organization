from __future__ import annotations

import argparse
import csv
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

from experiment.mmlu.r346_tool_backed_promptnode_local_preflight import _label, run_tool_promptnodes


DEFAULT_MMLU_TEST_DIR = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/datasets/MMLU/test"
DEFAULT_API_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r349_fresh_tool_promptnode_eval_api_manifest.jsonl"
DEFAULT_LOCAL_TOOL_JSONL = "experiment/mmlu/run_logs/mmlu_r349_fresh_tool_promptnode_eval_local_tool_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r349_fresh_tool_promptnode_eval_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r349_fresh_tool_promptnode_eval_preflight_report.md"

STEM_SUBJECTS = [
    "high_school_mathematics",
    "college_mathematics",
    "high_school_physics",
    "college_physics",
    "high_school_chemistry",
    "college_chemistry",
]
NONSTEM_SUBJECTS = [
    "business_ethics",
    "logical_fallacies",
    "philosophy",
    "moral_disputes",
    "professional_law",
    "high_school_us_history",
    "sociology",
    "world_religions",
]
EXCLUDED_JSONL_PATHS = [
    "experiment/mmlu/run_logs/mmlu_r304_multi_trigger_safety_gate_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r306_nonmath_stack_eval_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r312_nonstem_safety_replay_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r334_prospective_selector_eval_manifest.jsonl",
    "experiment/mmlu/run_logs/mmlu_r337_prospective_selector_eval_expand24_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r341_answer_bearing_candidate_generator_probe_manifest.jsonl",
    "experiment/mmlu/run_logs/mmlu_r342_answer_bearing_candidate_generator_api_probe_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r346_tool_backed_promptnode_local_preflight_results.jsonl",
    "experiment/mmlu/run_logs/mmlu_r347_tool_backed_promptnode_prospective_replay24_results.jsonl",
]
FORBIDDEN_PROMPT_FIELDS = {"task_id", "true_answer", "gold_answer", "is_correct", "evaluation_only", "source_ref_hash"}


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    p = _repo_path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def _question(row: List[str]) -> str:
    return "\n".join(
        [
            row[0].strip(),
            f"Option A: {row[1].strip()}",
            f"Option B: {row[2].strip()}",
            f"Option C: {row[3].strip()}",
            f"Option D: {row[4].strip()}",
        ]
    )


def _used_task_ids(paths: Iterable[str]) -> set[str]:
    used = set()
    for path in paths:
        for row in _load_jsonl(path):
            task_id = str(row.get("task_id") or "")
            if task_id:
                used.add(task_id)
    return used


def _load_subject_records(root: str, subjects: List[str], family: str, per_subject: int, used: set[str]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    base = Path(root)
    for subject in subjects:
        csv_path = base / f"{subject}_test.csv"
        if not csv_path.exists():
            continue
        kept = 0
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            for row_index, row in enumerate(reader):
                if len(row) < 6:
                    continue
                canonical = f"MMLU-{subject}_test-{row_index}"
                nonstem = f"MMLU-nonstem-{subject}_test-{row_index}"
                task_id = canonical if family == "mmlu_stem" else nonstem
                if canonical in used or nonstem in used or task_id in used:
                    continue
                records.append(
                    {
                        "run_id": "R349",
                        "task_id": task_id,
                        "dataset_family": family,
                        "subject": subject,
                        "row_index": row_index,
                        "question": _question(row),
                        "evaluation_only": {"true_answer": str(row[5]).strip().upper()[:1]},
                    }
                )
                kept += 1
                if kept >= per_subject:
                    break
    return records


def _api_messages(question: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "You are an ARG-Designer-compatible baseline solver for MMLU multiple-choice questions.",
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Solve this multiple-choice item using only the visible question.",
                    question,
                    "Return compact JSON with keys selected_label, confidence, rationale.",
                ]
            ),
        },
    ]


def _api_record(task: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "run_id": "R349",
        "task_id": task["task_id"],
        "dataset_family": task["dataset_family"],
        "subject": task["subject"],
        "row_index": task["row_index"],
        "control_variant": "arg_baseline_direct_api",
        "evaluation_only": task["evaluation_only"],
        "model_visible_messages": _api_messages(task["question"]),
        "api_required": True,
        "max_completion_tokens": 160,
        "model": "gpt-4o-2024-08-06",
    }


def _local_tool_record(task: Dict[str, Any]) -> Dict[str, Any]:
    result = run_tool_promptnodes(task["question"])
    candidate = _label(result.get("candidate_label"))
    true_answer = _label(task.get("evaluation_only", {}).get("true_answer"))
    return {
        "run_id": "R349",
        "task_id": task["task_id"],
        "dataset_family": task["dataset_family"],
        "subject": task["subject"],
        "row_index": task["row_index"],
        "control_variant": "frozen_tool_promptnode_local",
        "candidate_label": candidate,
        "promptnode_id": result.get("promptnode_id"),
        "promptedge_contract_pass": bool(result.get("promptedge_contract_pass")),
        "candidate_is_correct": candidate == true_answer if candidate else False,
        "evaluation_only": task["evaluation_only"],
        "evidence": result.get("evidence"),
    }


def _leakage(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    violations = []
    for row in rows:
        prompt = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", [])).lower()
        for field in FORBIDDEN_PROMPT_FIELDS:
            if field.lower() in prompt:
                violations.append({"task_id": row.get("task_id", ""), "field": field})
    return violations


def build_fresh_preflight(mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    used = _used_task_ids(EXCLUDED_JSONL_PATHS)
    stem = _load_subject_records(mmlu_test_dir, STEM_SUBJECTS, "mmlu_stem", 4, used)[:24]
    nonstem = _load_subject_records(mmlu_test_dir, NONSTEM_SUBJECTS, "mmlu_nonstem", 3, used)[:24]
    tasks = stem + nonstem
    api_records = [_api_record(task) for task in tasks]
    local_records = [_local_tool_record(task) for task in tasks]
    violations = _leakage(api_records)
    task_ids = {task["task_id"] for task in tasks}
    overlap = task_ids & used
    family_counts = Counter(task["dataset_family"] for task in tasks)
    forwarded = [row for row in local_records if row.get("candidate_label")]
    summary = {
        "run_id": "R349",
        "title": "Fresh frozen-policy tool PromptNode eval preflight",
        "claim_boundary": (
            "R349 builds a fresh 48-task MMLU manifest for the policy frozen at R347. It performs local tool "
            "preflight only; API execution is deferred to the next non-audit run."
        ),
        "no_api": True,
        "broad_api": False,
        "policy_frozen_after_run": "R347",
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
        "uses_true_answers_in_prompt": False,
        "uses_true_answers_in_tool": False,
        "api_execution_authorized_next": not violations and len(tasks) == 48 and not overlap,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R350_goal_audit_after_tool_promptnode_fresh_preflight",
    }
    return api_records, local_records, summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R349 Fresh Tool PromptNode Eval Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- Family counts: `{summary['task_family_counts']}`",
            f"- API calls planned: `{summary['api_calls_planned']}`",
            f"- Local tool forwarded candidates: `{summary['local_tool_forwarded_candidate_count']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- Overlap with excluded tasks: `{summary['overlap_with_excluded_task_count']}`",
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
    parser = argparse.ArgumentParser(description="Build R349 fresh tool PromptNode eval preflight.")
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
