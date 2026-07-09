from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R287 = "experiment/mmlu/res_logs/mmlu_r287_constrained_promptnode_decoding_c64_summary.json"
DEFAULT_R289_ROWS = "experiment/mmlu/run_logs/mmlu_r289_constrained_graph_api_full24_results.jsonl"
DEFAULT_BASELINE_ROWS = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl"
DEFAULT_SUMMARY = "experiment/mmlu/res_logs/mmlu_r290_goal_audit_after_r289_summary.json"
DEFAULT_REPORT = "experiment/mmlu/run_logs/mmlu_r290_goal_audit_after_r289_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        f.write(text)


def _task_id(row: Dict[str, Any]) -> str:
    return str(row.get("task_id") or row.get("id"))


def build_goal_audit(
    r287: Dict[str, Any],
    r289_rows: List[Dict[str, Any]],
    baseline_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    baseline_by_id = {_task_id(row): row for row in baseline_rows}
    matched = [(row, baseline_by_id.get(_task_id(row))) for row in r289_rows]
    matched = [(row, base) for row, base in matched if base is not None]

    r289_correct = sum(1 for row in r289_rows if row.get("is_correct"))
    baseline_correct = sum(1 for _row, base in matched if base.get("is_correct"))
    fixes = [
        row
        for row, base in matched
        if not base.get("is_correct") and row.get("is_correct")
    ]
    harms = [
        row
        for row, base in matched
        if base.get("is_correct") and not row.get("is_correct")
    ]
    wrong = [row for row in r289_rows if not row.get("is_correct")]
    transfer_superiority = len(matched) > 0 and r289_correct > baseline_correct and len(harms) == 0
    return {
        "run_id": "R290",
        "title": "Goal audit after R289 constrained PromptNode API replay",
        "claim_boundary": (
            "Goal/result audit only. R289 is compared to the existing R162 ARG transfer "
            "records on matched task_ids; R282 retrained ARG baseline is still required."
        ),
        "no_api": True,
        "broad_api": False,
        "goal_alignment": (
            "aligned_positive_transfer_result"
            if transfer_superiority
            else "aligned_negative_transfer_result"
        ),
        "r287_selected_contract_ready_rate": r287.get("selected_contract_ready_rate"),
        "matched_tasks": len(matched),
        "r289_records": len(r289_rows),
        "r289_correct": r289_correct,
        "r289_accuracy": r289_correct / len(r289_rows) if r289_rows else None,
        "baseline_correct_on_matched_tasks": baseline_correct,
        "baseline_accuracy_on_matched_tasks": baseline_correct / len(matched) if matched else None,
        "fixes_vs_baseline": len(fixes),
        "harms_vs_baseline": len(harms),
        "fix_task_ids": [_task_id(row) for row in fixes],
        "harm_task_ids": [_task_id(row) for row in harms],
        "wrong_task_ids": [_task_id(row) for row in wrong],
        "transfer_superiority_claim_supported": transfer_superiority,
        "sci_q2_ready": False,
        "main_decision": (
            "Do not claim MMLU transfer improvement. The graph structure gate improved, "
            "but terminal-only router replay underperforms the existing ARG transfer baseline "
            "on matched tasks."
        ),
        "next_runs": [
            "R291_all_exposure_replay",
            "R292_r282_arg_retrain_first24_api_baseline",
            "R293_failure_analysis_terminal_router_harms",
            "R294_decision_policy_revision",
            "R295_goal_audit",
        ],
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R290 Goal Audit After R289",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Goal alignment: `{summary['goal_alignment']}`",
            f"- R287 selected contract-ready rate: `{summary['r287_selected_contract_ready_rate']}`",
            f"- Matched tasks vs R162: `{summary['matched_tasks']}`",
            f"- R289 correct: `{summary['r289_correct']}/{summary['r289_records']}`",
            f"- R162 matched correct: `{summary['baseline_correct_on_matched_tasks']}/{summary['matched_tasks']}`",
            f"- Fix/harm vs R162: `{summary['fixes_vs_baseline']}/{summary['harms_vs_baseline']}`",
            f"- Transfer superiority claim supported: `{summary['transfer_superiority_claim_supported']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            "",
            "## Harm Task IDs",
            "",
            *[f"- `{task_id}`" for task_id in summary["harm_task_ids"]],
            "",
            "## Wrong Task IDs",
            "",
            *[f"- `{task_id}`" for task_id in summary["wrong_task_ids"]],
            "",
            "## Decision",
            "",
            summary["main_decision"],
            "",
            "## Next Runs",
            "",
            *[f"- `{run}`" for run in summary["next_runs"]],
            "",
        ]
    )


def run(
    r287_json: str = DEFAULT_R287,
    r289_rows_jsonl: str = DEFAULT_R289_ROWS,
    baseline_rows_jsonl: str = DEFAULT_BASELINE_ROWS,
    summary_json: str = DEFAULT_SUMMARY,
    report_md: str = DEFAULT_REPORT,
) -> Dict[str, Any]:
    summary = build_goal_audit(
        r287=_load_json(r287_json),
        r289_rows=_load_jsonl(r289_rows_jsonl),
        baseline_rows=_load_jsonl(baseline_rows_jsonl),
    )
    summary.update(
        {
            "source_files": {
                "r287": r287_json,
                "r289_rows": r289_rows_jsonl,
                "baseline_rows": baseline_rows_jsonl,
            },
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R290 goal audit after R289.")
    parser.add_argument("--r287_json", default=DEFAULT_R287)
    parser.add_argument("--r289_rows_jsonl", default=DEFAULT_R289_ROWS)
    parser.add_argument("--baseline_rows_jsonl", default=DEFAULT_BASELINE_ROWS)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY)
    parser.add_argument("--report_md", default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
