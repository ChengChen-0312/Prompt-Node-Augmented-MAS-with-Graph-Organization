from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from experiment.aqua.r267_cost_safety_combined_selector import (
    build_r267_summary,
    load_jsonl,
    normalize_label,
    write_json,
    write_text,
)


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_ARG_JSONL = os.path.join(SCRIPT_DIR, "aqua_tail34_arg_baseline_results.jsonl")
DEFAULT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "res_logs", "aqua_tail34_r269_critical_smoke_replay_summary.json")
DEFAULT_REPORT_MD = os.path.join(SCRIPT_DIR, "run_logs", "aqua_tail34_r269_critical_smoke_replay.md")

CRITICAL_TASKS = ["task_114", "task_59", "task_108", "task_250", "task_8", "task_188"]


def _fix_harm(task_outcomes: Dict[str, Dict[str, Any]], correctness_key: str) -> Dict[str, Any]:
    fixes = []
    harms = []
    for task_id, row in task_outcomes.items():
        baseline_correct = bool(row["baseline_official_correct"])
        selected_correct = bool(row[correctness_key])
        if not baseline_correct and selected_correct:
            fixes.append(task_id)
        if baseline_correct and not selected_correct:
            harms.append(task_id)
    return {
        "fixes": fixes,
        "harms": harms,
        "fix_harm": f"{len(fixes)}/{len(harms)}",
    }


def build_r269_summary() -> Dict[str, Any]:
    r267 = build_r267_summary()
    r267_by_task = {row["task_id"]: row for row in r267["records"]}
    arg_by_task = {row["task_id"]: row for row in load_jsonl(DEFAULT_ARG_JSONL)}
    task_outcomes: Dict[str, Dict[str, Any]] = {}
    for task_id in CRITICAL_TASKS:
        if task_id not in r267_by_task or task_id not in arg_by_task:
            continue
        selected = r267_by_task[task_id]
        baseline = arg_by_task[task_id]
        gold = normalize_label(selected["true_answer"])
        corrected_gold = "C" if task_id == "task_114" else gold
        baseline_pred = normalize_label(baseline.get("predicted_answer"))
        r267_pred = normalize_label(selected.get("predicted_answer"))
        task_outcomes[task_id] = {
            "task_id": task_id,
            "gold_official": gold,
            "gold_corrected_for_sensitivity": corrected_gold,
            "baseline_prediction": baseline_pred,
            "r267_prediction": r267_pred,
            "selected_source": selected.get("selected_source"),
            "baseline_official_correct": baseline_pred == gold,
            "r267_official_correct": r267_pred == gold,
            "correct_if_task114_label_corrected_to_c": r267_pred == corrected_gold,
            "interpretation": _interpret_task(task_id, baseline_pred, r267_pred),
        }
    official = _fix_harm(task_outcomes, "r267_official_correct")
    corrected = _fix_harm(task_outcomes, "correct_if_task114_label_corrected_to_c")
    return {
        "run_id": "R269",
        "title": "Critical case replay for R267",
        "claim_boundary": "no_api_critical_case_replay",
        "critical_tasks": list(task_outcomes),
        "task_outcomes": task_outcomes,
        "critical_official": official,
        "critical_task114_corrected": corrected,
        "next_action": "Use this as preflight evidence only; fresh API is still required before a deployable student selector claim.",
    }


def _interpret_task(task_id: str, baseline_prediction: str, r267_prediction: str) -> str:
    if task_id == "task_114":
        return "R267 suppresses the weak R065/R068 switch and keeps ARG's C, which is official-wrong but audit-correct under strict-bound math."
    if task_id == "task_59":
        return "R267 suppresses a weak switch on a disputed question-rationale row."
    if task_id == "task_108":
        return "R267 keeps a noisy-boundary fix because baseline direct votes split."
    if task_id == "task_250":
        return "R267 keeps the clean fix because objective evidence is strong."
    return f"R267 leaves the baseline prediction {baseline_prediction} as {r267_prediction}; this is a clean-harm guard case."


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# R269 Critical Smoke Replay",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Task | ARG | R267 | Official gold | R267 official | R267 corrected/sensitivity | Source |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for task_id, row in summary["task_outcomes"].items():
        lines.append(
            f"| `{task_id}` | `{row['baseline_prediction']}` | `{row['r267_prediction']}` | `{row['gold_official']}` | `{row['r267_official_correct']}` | `{row['correct_if_task114_label_corrected_to_c']}` | `{row['selected_source']}` |"
        )
    lines.extend(
        [
            "",
            f"- Critical official fix/harm: `{summary['critical_official']['fix_harm']}`",
            f"- Critical task114-corrected fix/harm: `{summary['critical_task114_corrected']['fix_harm']}`",
            "",
            summary["next_action"],
            "",
        ]
    )
    return "\n".join(lines)


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_r269_summary()
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
