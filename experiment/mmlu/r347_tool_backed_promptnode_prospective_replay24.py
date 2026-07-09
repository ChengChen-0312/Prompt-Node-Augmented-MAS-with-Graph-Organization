from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r346_tool_backed_promptnode_local_preflight import _label, _visible_item, run_tool_promptnodes


DEFAULT_R337_RESULTS = "experiment/mmlu/run_logs/mmlu_r337_prospective_selector_eval_expand24_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r347_tool_backed_promptnode_prospective_replay24_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r347_tool_backed_promptnode_prospective_replay24_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r347_tool_backed_promptnode_prospective_replay24_report.md"


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


def build_replay24(r337_results: str = DEFAULT_R337_RESULTS) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _load_jsonl(r337_results)
    baseline_rows = [row for row in rows if row.get("control_variant") == "arg_baseline_direct"]
    selector_by_task = {row.get("task_id"): row for row in rows if row.get("control_variant") == "selector_promptnode_promptedge_policy"}
    records = []
    for baseline_row in baseline_rows:
        task_id = baseline_row.get("task_id")
        selector_row = selector_by_task.get(task_id, baseline_row)
        item = _visible_item(selector_row)
        tool_result = run_tool_promptnodes(item)
        baseline_prediction = _label(baseline_row.get("predicted_answer") or baseline_row.get("baseline_prediction"))
        candidate = _label(tool_result.get("candidate_label"))
        true_answer = _label(baseline_row.get("true_answer"))
        final = candidate if candidate and tool_result.get("promptedge_contract_pass") else baseline_prediction
        records.append(
            {
                "run_id": "R347",
                "task_id": task_id,
                "subject": baseline_row.get("subject"),
                "baseline_prediction": baseline_prediction,
                "candidate_label": candidate,
                "promptnode_id": tool_result.get("promptnode_id"),
                "promptedge_contract_pass": bool(tool_result.get("promptedge_contract_pass")),
                "final_prediction": final,
                "true_answer": true_answer,
                "baseline_correct": baseline_prediction == true_answer,
                "final_correct": final == true_answer,
                "fixes_baseline": baseline_prediction != true_answer and final == true_answer,
                "harms_baseline": baseline_prediction == true_answer and final != true_answer,
                "evidence": tool_result.get("evidence"),
            }
        )
    arg_correct = sum(1 for row in records if row["baseline_correct"])
    tool_correct = sum(1 for row in records if row["final_correct"])
    summary = {
        "run_id": "R347",
        "title": "Tool-backed PromptNode prospective replay on R337 24-task split",
        "claim_boundary": (
            "R347 replays the frozen R345/R346 tool-backed PromptNode policy over all 24 tasks from R337. Because "
            "the tool families were designed after inspecting R337 errors, this is positive mechanism evidence, not a main paper claim."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "arg_correct": arg_correct,
        "tool_promptnode_correct": tool_correct,
        "tool_promptnode_delta_correct": tool_correct - arg_correct,
        "accuracy": round(tool_correct / len(records), 6) if records else 0.0,
        "arg_accuracy": round(arg_correct / len(records), 6) if records else 0.0,
        "forwarded_candidate_count": sum(1 for row in records if row["candidate_label"]),
        "fixes": sum(1 for row in records if row["fixes_baseline"]),
        "harms": sum(1 for row in records if row["harms_baseline"]),
        "uses_true_answers_in_tool": False,
        "uses_task_ids_or_known_wrong_items": False,
        "claim_permissions": {
            "replay_mechanism_evidence_allowed": tool_correct > arg_correct,
            "main_paper_claim_allowed": False,
            "fresh_eval_required_before_claim": True,
            "sci_q2_ready": False,
        },
        "next_required_run": "R348_fresh_tool_promptnode_eval_design",
    }
    return records, summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R347 Tool-Backed PromptNode Prospective Replay24",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- ARG: `{summary['arg_correct']}/{summary['records']}`",
            f"- Tool PromptNode: `{summary['tool_promptnode_correct']}/{summary['records']}`",
            f"- Delta correct: `{summary['tool_promptnode_delta_correct']}`",
            f"- Fix/harm: `{summary['fixes']}/{summary['harms']}`",
            f"- Forwarded candidates: `{summary['forwarded_candidate_count']}`",
            f"- Main paper claim allowed: `{summary['claim_permissions']['main_paper_claim_allowed']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r337_results: str = DEFAULT_R337_RESULTS,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_replay24(r337_results=r337_results)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_jsonl(output_jsonl, records)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay R345/R346 tool-backed PromptNode policy over R337 24-task split.")
    parser.add_argument("--r337_results", default=DEFAULT_R337_RESULTS)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
