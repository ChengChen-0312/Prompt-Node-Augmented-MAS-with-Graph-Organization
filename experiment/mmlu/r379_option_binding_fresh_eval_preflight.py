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

from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import (
    DEFAULT_MMLU_TEST_DIR,
    EXCLUDED_JSONL_PATHS,
    _api_record,
    _leakage,
    _question,
    _used_task_ids,
)
from experiment.mmlu.r362_source_invariant_fresh_eval_preflight import EXTRA_EXCLUDED_JSONL_PATHS as R362_EXCLUDES


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r379_option_binding_fresh_eval_manifest.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r379_option_binding_fresh_eval_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r379_option_binding_fresh_eval_preflight_report.md"
SUBJECT = "high_school_us_history"
R374_MANIFEST = "experiment/mmlu/run_logs/mmlu_r374_history_guarded_fresh_eval_manifest.jsonl"
EXTRA_EXCLUDES = R362_EXCLUDES + [
    "experiment/mmlu/run_logs/mmlu_r362_source_invariant_fresh_eval_manifest.jsonl",
    "experiment/mmlu/run_logs/mmlu_r368_adversarial_verifier_preflight_manifest.jsonl",
    R374_MANIFEST,
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


def _load_history_tasks(root: str, count: int, used: set[str]) -> List[Dict[str, Any]]:
    csv_path = Path(root) / f"{SUBJECT}_test.csv"
    tasks: List[Dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row_index, row in enumerate(reader):
            if len(row) < 6:
                continue
            canonical = f"MMLU-{SUBJECT}_test-{row_index}"
            nonstem = f"MMLU-nonstem-{SUBJECT}_test-{row_index}"
            if canonical in used or nonstem in used:
                continue
            tasks.append(
                {
                    "run_id": "R379",
                    "task_id": nonstem,
                    "dataset_family": "mmlu_nonstem",
                    "subject": SUBJECT,
                    "row_index": row_index,
                    "question": _question(row),
                    "evaluation_only": {"true_answer": str(row[5]).strip().upper()[:1]},
                }
            )
            if len(tasks) >= count:
                break
    return tasks


def _option_binding_messages(question: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a HistoryVerifierPN followed by an OptionBinding PromptEdge and a SafetyGatePN. "
                "Use only the visible source text, question, and options."
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Visible multiple-choice item:",
                    question,
                    "",
                    "Graph path:",
                    "1. HistoryVerifierPN reads the passage and options.",
                    "2. OptionBindingPromptEdge may bind exactly one Option A/B/C/D/E into candidate_label only when the rationale explicitly supports that option.",
                    "3. SafetyGatePN will later decide whether the bound label is forwarded; do not force a label.",
                    "",
                    "Rules:",
                    "- If no option is directly supported, leave candidate_label empty.",
                    "- If you name an option in the rationale as the supported answer, candidate_label must be that option label.",
                    "- Set promptedge_contract_pass true only when candidate_label is nonempty, confidence >= 0.85, and evidence_count >= 1.",
                    "",
                    "Return compact JSON with keys candidate_label, confidence, evidence_count, promptnode_family, candidate_type, promptedge_contract_pass, rationale.",
                ]
            ),
        },
    ]


def _option_binding_record(task: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "run_id": "R379",
        "task_id": task["task_id"],
        "dataset_family": task["dataset_family"],
        "subject": task["subject"],
        "row_index": task["row_index"],
        "control_variant": "history_option_binding_candidate_api",
        "evaluation_only": task["evaluation_only"],
        "model_visible_messages": _option_binding_messages(task["question"]),
        "api_required": True,
        "max_completion_tokens": 220,
        "model": "gpt-4o-2024-08-06",
    }


def build_option_binding_preflight(mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    used = _used_task_ids(EXCLUDED_JSONL_PATHS + EXTRA_EXCLUDES)
    r374_used = _used_task_ids([R374_MANIFEST])
    tasks = _load_history_tasks(mmlu_test_dir, 24, used)
    records: List[Dict[str, Any]] = []
    for task in tasks:
        arg = _api_record(task)
        arg["run_id"] = "R379"
        arg["control_variant"] = "arg_baseline_direct_api"
        records.append(arg)
        records.append(_option_binding_record(task))
    violations = _leakage(records)
    variants = Counter(row["control_variant"] for row in records)
    selected_ids = {task["task_id"] for task in tasks}
    return records, {
        "run_id": "R379",
        "title": "OptionBinding fresh eval preflight",
        "claim_boundary": (
            "R379 builds a fresh manifest that includes the OptionBinding PromptEdge from the start. "
            "It does not execute API or support a paper claim."
        ),
        "no_api": True,
        "broad_api": False,
        "subject": SUBJECT,
        "tasks": len(tasks),
        "api_records": len(records),
        "planned_arg_baseline_calls": variants.get("arg_baseline_direct_api", 0),
        "planned_option_binding_candidate_calls": variants.get("history_option_binding_candidate_api", 0),
        "variant_counts": dict(sorted(variants.items())),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "r374_overlap_free": not bool(selected_ids & r374_used),
        "api_execution_authorized_next": not violations and len(tasks) == 24 and not bool(selected_ids & r374_used),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R380_option_binding_fresh_eval_api_execution",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R379 OptionBinding Fresh Eval Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- API records: `{summary['api_records']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            f"- R374 overlap free: `{summary['r374_overlap_free']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    mmlu_test_dir: str = DEFAULT_MMLU_TEST_DIR,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_option_binding_preflight(mmlu_test_dir=mmlu_test_dir)
    summary.update({"manifest_jsonl": manifest_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(manifest_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R379 OptionBinding fresh eval preflight.")
    parser.add_argument("--mmlu_test_dir", default=DEFAULT_MMLU_TEST_DIR)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
