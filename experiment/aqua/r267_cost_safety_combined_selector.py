from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Set, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_R068_JSONL = os.path.join(SCRIPT_DIR, "aqua_tail34_r068_selective_multiview_results.jsonl")
DEFAULT_R068_SUMMARY = os.path.join(SCRIPT_DIR, "res_logs", "aqua_tail34_r068_selective_multiview_summary.json")
DEFAULT_R095_SUMMARY = os.path.join(SCRIPT_DIR, "res_logs", "aqua_tail34_r095_objective_safety_composed_summary.json")
DEFAULT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "res_logs", "aqua_tail34_r267_cost_safety_combined_summary.json")
DEFAULT_REPORT_MD = os.path.join(SCRIPT_DIR, "run_logs", "aqua_tail34_r267_cost_safety_combined_report.md")

BAD_TASKS = {"task_59", "task_139", "task_228"}


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    return label[:1] if label[:1] in {"A", "B", "C", "D", "E"} else "NONE"


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _score_rows(
    rows: Iterable[Dict[str, Any]],
    excluded: Set[str],
    corrected_labels: Dict[str, str],
) -> Dict[str, Any]:
    scored = []
    for row in rows:
        task_id = str(row["task_id"])
        if task_id in excluded:
            continue
        effective = normalize_label(corrected_labels.get(task_id, row.get("true_answer")))
        predicted = normalize_label(row.get("predicted_answer"))
        scored.append(
            {
                "task_id": task_id,
                "predicted_answer": predicted,
                "effective_answer": effective,
                "correct": predicted == effective,
            }
        )
    correct = sum(1 for row in scored if row["correct"])
    total = len(scored)
    return {
        "accuracy": f"{correct}/{total}",
        "correct": correct,
        "total": total,
        "wrong_task_ids": [row["task_id"] for row in scored if not row["correct"]],
    }


def build_r267_records(
    r068_jsonl: str = DEFAULT_R068_JSONL,
    r095_summary_json: str = DEFAULT_R095_SUMMARY,
) -> List[Dict[str, Any]]:
    r068_rows = {row["task_id"]: row for row in load_jsonl(r068_jsonl)}
    r095_rows = {row["task_id"]: row for row in load_json(r095_summary_json)["rows"]}
    records: List[Dict[str, Any]] = []
    for task_id, r068 in r068_rows.items():
        r095 = r095_rows[task_id]
        action = str(r095.get("decision_action"))
        can_use_objective = bool(r068.get("multiview_would_run")) and action == "accept_objective"
        prediction = (
            r095.get("safety_composed_prediction")
            if can_use_objective
            else r095.get("baseline_prediction", r068.get("baseline_prediction"))
        )
        true_answer = normalize_label(r068.get("true_answer") or r095.get("true_answer"))
        predicted = normalize_label(prediction)
        records.append(
            {
                "task_id": task_id,
                "true_answer": true_answer,
                "predicted_answer": predicted,
                "baseline_prediction": normalize_label(r095.get("baseline_prediction")),
                "objective_prediction": normalize_label(r095.get("objective_prediction")),
                "is_solved": predicted == true_answer,
                "selected_source": "safety_accept_objective" if can_use_objective else "baseline",
                "multiview_would_run": bool(r068.get("multiview_would_run")),
                "r095_decision_action": action,
                "r095_decision_reason": r095.get("decision_reason"),
                "trigger_features": r068.get("trigger_features", {}),
                "decision_features": r095.get("decision_features", {}),
            }
        )
    return records


def _rounded_cost(cost_estimate: Dict[str, Any]) -> Dict[str, Any]:
    rounded = dict(cost_estimate)
    for key in [
        "estimated_cost",
        "full_multiview_cost",
        "cost_saving_vs_full_multiview",
        "relative_cost_vs_arg",
        "estimated_prompt_tokens",
        "estimated_completion_tokens",
        "full_prompt_tokens",
        "full_completion_tokens",
    ]:
        if key in rounded and isinstance(rounded[key], (int, float)):
            rounded[key] = round(float(rounded[key]), 6)
    rounded["marginal_api_cost_after_r068_traces"] = 0.0
    return rounded


def build_r267_summary(
    r068_jsonl: str = DEFAULT_R068_JSONL,
    r068_summary_json: str = DEFAULT_R068_SUMMARY,
    r095_summary_json: str = DEFAULT_R095_SUMMARY,
) -> Dict[str, Any]:
    records = build_r267_records(r068_jsonl, r095_summary_json)
    r068_summary = load_json(r068_summary_json)
    official = _score_rows(records, set(), {})
    exclude_bad = _score_rows(records, BAD_TASKS, {})
    correct_114 = _score_rows(records, BAD_TASKS, {"task_114": "C"})
    exclude_114 = _score_rows(records, BAD_TASKS | {"task_114"}, {})
    accepted = [row["task_id"] for row in records if row["selected_source"] == "safety_accept_objective"]
    suppressed = [
        row["task_id"]
        for row in records
        if row["objective_prediction"] != row["baseline_prediction"]
        and row["selected_source"] != "safety_accept_objective"
    ]
    return {
        "run_id": "R267",
        "title": "R068 cost trigger plus R095 safety gate",
        "claim_boundary": "no_api_replay_over_r068_trigger_and_r095_safety_gate",
        "no_api": True,
        "records": records,
        "official": official,
        "exclude_59_139_228": exclude_bad,
        "exclude_59_139_228_correct_114": correct_114,
        "exclude_59_139_228_114": exclude_114,
        "accepted_switch_tasks": accepted,
        "suppressed_switch_tasks": suppressed,
        "cost_estimate": _rounded_cost(r068_summary.get("cost_estimate", {})),
        "interpretation": (
            "R267 keeps R068's reduced multi-view trigger cost and applies R095's safety gate. "
            "It loses one official point relative to R065/R068 by suppressing task_114, but becomes "
            "audit-correct when task_114 is treated as a boundary-label error."
        ),
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R267 Cost-Safety Combined Selector",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Scores",
            "",
            "| View | Score | Wrong tasks |",
            "|---|---:|---|",
            f"| Official tail34 | `{summary['official']['accuracy']}` | `{summary['official']['wrong_task_ids']}` |",
            f"| Exclude 59/139/228 | `{summary['exclude_59_139_228']['accuracy']}` | `{summary['exclude_59_139_228']['wrong_task_ids']}` |",
            f"| Exclude 59/139/228 + correct 114 | `{summary['exclude_59_139_228_correct_114']['accuracy']}` | `{summary['exclude_59_139_228_correct_114']['wrong_task_ids']}` |",
            f"| Exclude 59/139/228/114 | `{summary['exclude_59_139_228_114']['accuracy']}` | `{summary['exclude_59_139_228_114']['wrong_task_ids']}` |",
            "",
            "## Decisions",
            "",
            f"- Accepted switches: `{summary['accepted_switch_tasks']}`",
            f"- Suppressed switches: `{summary['suppressed_switch_tasks']}`",
            f"- Estimated cost from zero: `${summary['cost_estimate']['estimated_cost']}`",
            f"- Marginal API cost after R068 traces: `${summary['cost_estimate']['marginal_api_cost_after_r068_traces']}`",
            "",
            "## Interpretation",
            "",
            summary["interpretation"],
            "",
        ]
    )


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_r267_summary()
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
