from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r301_conservative_census_gate import (
    VALID_LABELS,
    load_jsonl,
    normalize_label,
    write_json,
    write_jsonl,
    write_text,
)
from experiment.mmlu.r306_nonmath_stack_eval import should_forward_nonmath


DEFAULT_R306_JSONL = "experiment/mmlu/run_logs/mmlu_r306_nonmath_stack_eval_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r309_negative_controls_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r309_negative_controls_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r309_negative_controls_report.md"

CONTROL_NAMES = [
    "no_nonmath_promptnodes",
    "random_forward_same_budget",
    "always_forward_candidate_nodes",
    "no_safety_gate_unsafe_forward",
    "random_promptnode_type_same_budget",
    "no_lifecycle_prune_disabled",
]
NON_ANSWER_TYPES = [
    "instruction_ambiguity_verifier",
    "memory_bridge_required",
    "consensus_conflict_resolver",
    "adversarial_verifier",
]


def _valid_label(value: Any) -> str:
    label = normalize_label(value)
    return label if label in VALID_LABELS else ""


def _current(row: Dict[str, Any]) -> str:
    return _valid_label(row.get("r304_prediction") or row.get("arg_prediction") or row.get("predicted_answer"))


def _official(row: Dict[str, Any]) -> str:
    return _valid_label(row.get("true_answer"))


def _clean(row: Dict[str, Any]) -> str:
    return _valid_label(row.get("audit_clean_answer") or row.get("true_answer"))


def _candidate(row: Dict[str, Any]) -> Dict[str, Any]:
    candidate = row.get("candidate")
    return candidate if isinstance(candidate, dict) else {}


def _candidate_available(row: Dict[str, Any]) -> bool:
    return str(_candidate(row).get("candidate_type") or "none") != "none"


def _candidate_label(row: Dict[str, Any]) -> str:
    return _valid_label(_candidate(row).get("candidate_label"))


def _answer_bearing_candidate(row: Dict[str, Any]) -> bool:
    label = _candidate_label(row)
    return bool(label) and label != _current(row)


def _next_label(label: str) -> str:
    labels = ["A", "B", "C", "D"]
    if label not in labels:
        return "A"
    return labels[(labels.index(label) + 1) % len(labels)]


def _random_non_current_label(rng: random.Random, current: str) -> str:
    labels = [label for label in ["A", "B", "C", "D"] if label != current]
    return rng.choice(labels)


def _selected_random_tasks(source_rows: List[Dict[str, Any]], budget: int, seed: int) -> Dict[str, str]:
    rng = random.Random(seed)
    eligible = sorted(
        [row for row in source_rows if not row.get("audit_excluded") and _candidate_available(row)],
        key=lambda row: str(row.get("task_id") or ""),
    )
    selected = rng.sample(eligible, min(budget, len(eligible))) if eligible and budget > 0 else []
    return {str(row.get("task_id") or ""): _random_non_current_label(rng, _current(row)) for row in selected}


def _mutated_type_by_task(source_rows: List[Dict[str, Any]], budget: int, seed: int) -> Dict[str, str]:
    rng = random.Random(seed)
    forwarded = sorted(
        [row for row in source_rows if not row.get("audit_excluded") and row.get("nonmath_forward")],
        key=lambda row: str(row.get("task_id") or ""),
    )
    out: Dict[str, str] = {}
    for row in forwarded[:budget]:
        current_type = str(_candidate(row).get("candidate_type") or "")
        choices = [name for name in NON_ANSWER_TYPES if name != current_type]
        out[str(row.get("task_id") or "")] = rng.choice(choices)
    return out


def _score_prediction(row: Dict[str, Any], predicted: str) -> Dict[str, Any]:
    current = _current(row)
    official = _official(row)
    clean = _clean(row)
    baseline_official = current == official if official else None
    baseline_clean = current == clean if clean else None
    official_correct = predicted == official if official else None
    clean_correct = predicted == clean if clean else None
    return {
        "is_correct": official_correct,
        "audit_clean_is_correct": clean_correct,
        "fix": baseline_official is False and official_correct is True,
        "harm": baseline_official is True and official_correct is False,
        "audit_clean_fix": baseline_clean is False and clean_correct is True,
        "audit_clean_harm": baseline_clean is True and clean_correct is False,
        "answer_switch": predicted != current,
    }


def _control_prediction(
    control: str,
    row: Dict[str, Any],
    random_task_to_label: Dict[str, str],
    mutated_type_by_task: Dict[str, str],
) -> Tuple[str, bool, str]:
    current = _current(row)
    task_id = str(row.get("task_id") or "")
    candidate = dict(_candidate(row))
    label = _candidate_label(row)
    available = _candidate_available(row)

    if row.get("audit_excluded"):
        return current, False, "audit_excluded_keep_r304"
    if control == "no_nonmath_promptnodes":
        return current, False, "keep_r304_no_nonmath"
    if control == "random_forward_same_budget":
        if task_id in random_task_to_label:
            return random_task_to_label[task_id], True, "random_answer_forward"
        return current, False, "keep_r304_random_budget"
    if control == "always_forward_candidate_nodes":
        if not available:
            return current, False, "no_candidate"
        if label and label != current:
            return label, True, "always_forward_answer_candidate"
        return current, True, "always_forward_signal_only"
    if control == "no_safety_gate_unsafe_forward":
        if not available:
            return current, False, "no_candidate"
        if label and label != current:
            return label, True, "ungated_answer_candidate"
        return _next_label(current), True, "ungated_unresolved_signal_to_answer"
    if control == "random_promptnode_type_same_budget":
        if task_id in mutated_type_by_task:
            candidate["candidate_type"] = mutated_type_by_task[task_id]
            if should_forward_nonmath(candidate, current):
                return normalize_label(candidate.get("candidate_label")), True, "mutated_type_forwarded"
            return current, False, "mutated_type_rejected"
        return current, False, "keep_r304_type_budget"
    if control == "no_lifecycle_prune_disabled":
        if not available:
            return current, False, "no_candidate"
        if label and label != current:
            return label, True, "no_lifecycle_answer_candidate"
        return current, True, "no_lifecycle_unpruned_signal"
    raise ValueError(f"unknown control: {control}")


def build_control_records(source_rows: List[Dict[str, Any]], seed: int = 309) -> List[Dict[str, Any]]:
    main_budget = sum(1 for row in source_rows if not row.get("audit_excluded") and row.get("nonmath_forward"))
    random_task_to_label = _selected_random_tasks(source_rows, main_budget, seed)
    mutated_type_tasks = _mutated_type_by_task(source_rows, main_budget, seed + 1)
    records: List[Dict[str, Any]] = []
    for control in CONTROL_NAMES:
        for row in source_rows:
            current = _current(row)
            predicted, forwarded, decision_rule = _control_prediction(
                control,
                row,
                random_task_to_label=random_task_to_label,
                mutated_type_by_task=mutated_type_tasks,
            )
            scored = _score_prediction(row, predicted)
            records.append(
                {
                    "run_id": "R309",
                    "control": control,
                    "task_id": row.get("task_id"),
                    "audit_excluded": bool(row.get("audit_excluded")),
                    "r304_prediction": current,
                    "r306_prediction": normalize_label(row.get("predicted_answer")),
                    "predicted_answer": predicted,
                    "true_answer": _official(row),
                    "audit_clean_answer": _clean(row),
                    "candidate_type": str(_candidate(row).get("candidate_type") or "none"),
                    "candidate_label": _candidate_label(row),
                    "candidate_available": _candidate_available(row),
                    "answer_bearing_candidate": _answer_bearing_candidate(row),
                    "forwarded": forwarded,
                    "decision_rule": decision_rule,
                    "model_visible_features_only": True,
                    "claim_boundary": "R309 negative control; labels are used only after control predictions are fixed.",
                    **scored,
                }
            )
    return records


def _count(rows: Iterable[Dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if row.get(key))


def _summarize_slice(rows: List[Dict[str, Any]], prefix: str) -> Dict[str, Any]:
    official = [row for row in rows if row.get("is_correct") is not None]
    clean = [row for row in rows if row.get("audit_clean_is_correct") is not None]
    correct = _count(official, "is_correct")
    clean_correct = _count(clean, "audit_clean_is_correct")
    fixes = _count(official, "fix")
    harms = _count(official, "harm")
    clean_fixes = _count(clean, "audit_clean_fix")
    clean_harms = _count(clean, "audit_clean_harm")
    forwarded = _count(rows, "forwarded")
    cost_units = len(rows) + forwarded
    return {
        f"{prefix}_records": len(rows),
        f"{prefix}_correct": correct,
        f"{prefix}_accuracy": correct / len(official) if official else None,
        f"{prefix}97": f"{correct}/{len(rows)}" if prefix == "main" else f"{correct}/{len(rows)}",
        f"{prefix}_audit_clean_correct": clean_correct,
        f"{prefix}_audit_clean_accuracy": clean_correct / len(clean) if clean else None,
        f"{prefix}_fixes": fixes,
        f"{prefix}_harms": harms,
        f"{prefix}_fix_harm": f"{fixes}/{harms}",
        f"{prefix}_audit_clean_fixes": clean_fixes,
        f"{prefix}_audit_clean_harms": clean_harms,
        f"{prefix}_audit_clean_fix_harm": f"{clean_fixes}/{clean_harms}",
        f"{prefix}_forwarded": forwarded,
        f"{prefix}_answer_switches": _count(rows, "answer_switch"),
        f"{prefix}_cost_units": cost_units,
        f"{prefix}_cost_normalized_correct": correct / cost_units if cost_units else None,
    }


def _source_reference(source_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    main = [row for row in source_rows if not row.get("audit_excluded")]
    main_correct = _count(main, "is_correct")
    main_forwarded = _count(main, "nonmath_forward")
    main_cost_units = len(main) + main_forwarded
    return {
        "run": "R306",
        "r306_main97": f"{main_correct}/{len(main)}",
        "r306_main_correct": main_correct,
        "r306_main_records": len(main),
        "r306_main_forwarded": main_forwarded,
        "r306_main_answer_switches": sum(1 for row in main if _current(row) != normalize_label(row.get("predicted_answer"))),
        "r306_main_harms": _count(main, "harm"),
        "r306_main_cost_units": main_cost_units,
        "r306_main_cost_normalized_correct": main_correct / main_cost_units if main_cost_units else None,
    }


def build_negative_control_summary(records: List[Dict[str, Any]], source_rows: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    source_rows = source_rows or load_jsonl(DEFAULT_R306_JSONL)
    reference = _source_reference(source_rows)
    controls: Dict[str, Dict[str, Any]] = {}
    for control in CONTROL_NAMES:
        control_rows = [row for row in records if row.get("control") == control]
        main = [row for row in control_rows if not row.get("audit_excluded")]
        appendix = [row for row in control_rows if row.get("audit_excluded")]
        control_summary = {
            "control": control,
            "claim_boundary": "Negative control over fixed R306 candidates; no training and no API.",
        }
        control_summary.update(_summarize_slice(control_rows, "full"))
        control_summary.update(_summarize_slice(main, "main"))
        control_summary.update(_summarize_slice(appendix, "appendix"))
        controls[control] = control_summary

    r306_correct = reference["r306_main_correct"]
    r306_forwarded = reference["r306_main_forwarded"]
    cheap_threats = [
        name
        for name, data in controls.items()
        if data["main_correct"] >= r306_correct and data["main_forwarded"] <= r306_forwarded
    ]
    equal_accuracy_more_cost = [
        name
        for name, data in controls.items()
        if data["main_correct"] == r306_correct and data["main_forwarded"] > r306_forwarded
    ]
    return {
        "run_id": "R309",
        "title": "Negative controls for expanded PromptNode stack",
        "claim_boundary": (
            "R309 tests whether R306 can be explained by cheap random forwarding, always-forward routing, "
            "missing safety gates, random node identity, or disabled lifecycle. It does not authorize training."
        ),
        "no_api": True,
        "broad_api": False,
        "reference": reference,
        "controls": controls,
        "cheap_control_threats": cheap_threats,
        "cheap_control_matches_or_beats_r306": bool(cheap_threats),
        "equal_accuracy_more_cost_controls": equal_accuracy_more_cost,
        "negative_controls_passed_for_accuracy": not cheap_threats,
        "training_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R310_transfer_preflight",
        "next_required_actions": [
            "Replay the expanded node catalog on AQuA audit-clean tail34 and a non-STEM MMLU split.",
            "Keep training blocked until transfer is non-negative and ablations identify which PromptNode families contribute.",
            "Track cost-normalized accuracy because always-forward/no-lifecycle can tie accuracy with much higher routing cost.",
        ],
    }


def run_controls(r306_jsonl: str = DEFAULT_R306_JSONL, seed: int = 309) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    source_rows = load_jsonl(r306_jsonl)
    records = build_control_records(source_rows, seed=seed)
    summary = build_negative_control_summary(records, source_rows)
    return records, summary


def render_report(summary: Dict[str, Any]) -> str:
    ref = summary["reference"]
    rows = [
        "# R309 Negative Controls",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- R306 reference main97: `{ref['r306_main97']}` with `{ref['r306_main_forwarded']}` forwarded nodes",
        f"- Cheap control matches/beats R306: `{summary['cheap_control_matches_or_beats_r306']}`",
        f"- Equal-accuracy but higher-cost controls: `{summary['equal_accuracy_more_cost_controls']}`",
        "",
        "## Controls",
        "",
        "| control | main97 | fix/harm | forwarded | cost-norm |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, data in summary["controls"].items():
        rows.append(
            "| {name} | `{score}` | `{fix_harm}` | `{forwarded}` | `{cost_norm:.4f}` |".format(
                name=name,
                score=data["main97"],
                fix_harm=data["main_fix_harm"],
                forwarded=data["main_forwarded"],
                cost_norm=float(data["main_cost_normalized_correct"] or 0.0),
            )
        )
    rows.extend(["", "## Next", ""])
    rows.extend(f"- {action}" for action in summary["next_required_actions"])
    rows.append("")
    return "\n".join(rows)


def run(
    r306_jsonl: str = DEFAULT_R306_JSONL,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    seed: int = 309,
) -> Dict[str, Any]:
    records, summary = run_controls(r306_jsonl=r306_jsonl, seed=seed)
    summary.update(
        {
            "r306_jsonl": r306_jsonl,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
            "seed": seed,
        }
    )
    write_jsonl(output_jsonl, records)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R309 negative controls for expanded PromptNode stack.")
    parser.add_argument("--r306_jsonl", default=DEFAULT_R306_JSONL)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--seed", type=int, default=309)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
