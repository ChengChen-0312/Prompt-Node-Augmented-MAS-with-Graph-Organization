import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.contract_ablation_analysis import (  # noqa: E402
    load_audit_labels,
    summarize_variant_records,
)
from experiment.aqua.offline_utility_selector import normalize_option  # noqa: E402
from experiment.aqua.selective_multiview_trigger import ratio_text  # noqa: E402


RULE_NAME = "r073_surgical_cascade_trigger_replay"
BOUNDARY = "replay_over_r072_fresh_cascade_traces_not_new_api_run"
OUTCOME_FIELDS = {"true_answer", "is_solved", "baseline_is_solved", "task_id"}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_json(path: str, payload: Dict[str, Any]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, records: Iterable[Dict[str, Any]]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def should_run_surgical_trigger(features: Dict[str, Any]) -> bool:
    if bool(features.get("invalid_baseline_prediction")):
        return True
    return bool(
        features.get("weak_final_support")
        and features.get("low_direct_coverage")
        and int(features.get("non_promptnode_output_count") or 0) <= 2
        and not features.get("direct_conflict")
    )


def _decision_features(features: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "invalid_baseline_prediction",
        "weak_final_support",
        "low_direct_coverage",
        "non_promptnode_output_count",
        "direct_conflict",
        "missing_direct_vote_count",
        "final_direct_support_count",
        "direct_valid_vote_count",
    ]
    return {
        "rule": RULE_NAME,
        **{key: features.get(key) for key in keys},
    }


def build_surgical_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    selected = []
    for record in records:
        features = record.get("trigger_features", {}) or {}
        would_run = should_run_surgical_trigger(features)
        has_view_evidence = bool(record.get("multiview_was_run"))
        use_promptnode = would_run and has_view_evidence

        true_answer = normalize_option(record.get("true_answer"))
        baseline_prediction = normalize_option(record.get("baseline_prediction"))
        selected_prediction = normalize_option(
            record.get("predicted_answer") if use_promptnode else baseline_prediction
        )
        original_selected_prediction = normalize_option(record.get("predicted_answer"))
        selected_source = record.get("selected_source") if use_promptnode else "baseline"
        selected_method = record.get("selected_method") if use_promptnode else None
        view_calls = int(record.get("view_calls", 0)) if use_promptnode else 0
        full_view_count = int(record.get("full_view_count", 0)) if use_promptnode else 0

        selected.append(
            {
                "task_id": record.get("task_id"),
                "question": record.get("question"),
                "true_answer": true_answer,
                "predicted_answer": selected_prediction,
                "is_solved": selected_prediction == true_answer,
                "selected_source": selected_source,
                "selected_method": selected_method,
                "selection_rule": RULE_NAME,
                "surgical_would_run": would_run,
                "multiview_was_run": use_promptnode,
                "original_multiview_was_run": has_view_evidence,
                "baseline_prediction": baseline_prediction,
                "baseline_is_solved": bool(record.get("baseline_is_solved")),
                "original_selected_prediction": original_selected_prediction,
                "original_selected_source": record.get("selected_source"),
                "view_predictions": record.get("view_predictions", {}) if use_promptnode else {},
                "view_calls": view_calls,
                "full_view_count": full_view_count,
                "trigger_features": features,
                "decision_features": _decision_features(features),
            }
        )
    return selected


def summarize_surgical_records(
    records: List[Dict[str, Any]],
    audit_labels: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    audit_labels = audit_labels or {}
    total = len(records)
    solved = sum(1 for record in records if record.get("is_solved"))
    baseline = sum(1 for record in records if record.get("baseline_is_solved"))
    run_records = [record for record in records if record.get("multiview_was_run")]
    switch_records = [
        record
        for record in records
        if normalize_option(record.get("predicted_answer"))
        != normalize_option(record.get("baseline_prediction"))
    ]
    fixes = [
        record
        for record in records
        if not record.get("baseline_is_solved") and record.get("is_solved")
    ]
    harms = [
        record
        for record in records
        if record.get("baseline_is_solved") and not record.get("is_solved")
    ]
    view_calls = sum(int(record.get("view_calls", 0)) for record in records)
    full_view_count = sum(int(record.get("full_view_count", 0)) for record in records)
    posthoc = summarize_variant_records(RULE_NAME, records, audit_labels) if audit_labels else {}
    return {
        "rule": RULE_NAME,
        "total_tasks": total,
        "solved_tasks": solved,
        "baseline_solved_tasks": baseline,
        "overall": ratio_text(solved, total),
        "baseline": ratio_text(baseline, total),
        "delta_vs_baseline": solved - baseline,
        "multiview_run_count": len(run_records),
        "multiview_run": ratio_text(len(run_records), total),
        "view_call_count": view_calls,
        "full_view_count": full_view_count,
        "view_calls": ratio_text(view_calls, full_view_count),
        "switches": len(switch_records),
        "switch_tasks": [record["task_id"] for record in switch_records],
        "fixes": len(fixes),
        "harms": len(harms),
        "fix_harm": f"{len(fixes)}/{len(harms)}",
        "fix_tasks": [record["task_id"] for record in fixes],
        "harm_tasks": [record["task_id"] for record in harms],
        "run_tasks": [record["task_id"] for record in run_records],
        "posthoc_audit_summary": posthoc,
        **{
            key: posthoc[key]
            for key in [
                "clean",
                "noisy_or_ambiguous",
                "clean_fix_harm",
                "noisy_fix_harm",
            ]
            if key in posthoc
        },
    }


def estimate_surgical_cost(
    baseline_cost: float,
    reference_total_cost: float,
    reference_view_calls: int,
    surgical_view_calls: int,
) -> Dict[str, Any]:
    view_overhead = max(0.0, reference_total_cost - baseline_cost)
    per_view_overhead = view_overhead / reference_view_calls if reference_view_calls else 0.0
    estimated_cost = baseline_cost + per_view_overhead * surgical_view_calls
    return {
        "cost_model": "r059_baseline_plus_r072_measured_view_overhead_scaled_by_view_calls",
        "baseline_cost": round(baseline_cost, 6),
        "reference_total_cost": round(reference_total_cost, 6),
        "reference_view_calls": reference_view_calls,
        "surgical_view_calls": surgical_view_calls,
        "per_view_overhead": round(per_view_overhead, 6),
        "estimated_cost": round(estimated_cost, 6),
        "saving_vs_r072": round(reference_total_cost - estimated_cost, 6),
        "relative_cost_vs_arg": round(estimated_cost / baseline_cost, 2)
        if baseline_cost
        else None,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R073 Surgical Cascade Trigger Replay",
            "",
            f"**Boundary**: `{BOUNDARY}`. This is a replay over R072 fresh cascade traces, not a new API run.",
            "",
            "## Rule",
            "",
            "Run cascade views only when baseline is invalid, or when baseline has weak final support, low direct coverage, at most two non-PromptNode outputs, and no direct option conflict.",
            "",
            "## Summary",
            "",
            f"- Selected accuracy: `{summary['overall']}`",
            f"- Internal ARG baseline: `{summary['baseline']}`",
            f"- Delta vs baseline: `{summary['delta_vs_baseline']:+d}`",
            f"- Multi-view triggered tasks: `{summary['multiview_run']}`",
            f"- View calls: `{summary['view_calls']}`",
            f"- Switches: `{summary['switches']}`",
            f"- Fix/Harm: `{summary['fix_harm']}`",
            f"- Clean: `{summary.get('clean', 'n/a')}`",
            f"- Clean Fix/Harm: `{summary.get('clean_fix_harm', 'n/a')}`",
            f"- Estimated cost: `${summary.get('estimated_cost', 0.0):.6f}`",
            f"- Saving vs R072: `${summary.get('saving_vs_r072', 0.0):.6f}`",
            f"- Relative cost vs ARG: `{summary.get('relative_cost_vs_arg')}x`",
            "",
            "## Boundary",
            "",
            "R073 is a trigger-compression hypothesis. It can justify a fresh API run or train-time selector target, but it cannot be reported as measured billing.",
            "",
        ]
    )


def _absolute(path: Optional[str]) -> Optional[str]:
    if path is None or os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(REPO_ROOT, path))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay a surgical cascade trigger over R072 traces.")
    parser.add_argument(
        "--input-file",
        default="experiment/aqua/aqua_tail34_r072_integrated_cascade_results.jsonl",
    )
    parser.add_argument(
        "--audit-file",
        default="experiment/aqua/aqua_tail34_option_binding_audit.jsonl",
    )
    parser.add_argument("--baseline-cost", type=float, default=0.932850)
    parser.add_argument("--reference-total-cost", type=float, default=2.826040)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--report-md", required=True)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    args.input_file = _absolute(args.input_file)
    args.audit_file = _absolute(args.audit_file)
    args.output_file = _absolute(args.output_file)
    args.summary_json = _absolute(args.summary_json)
    args.report_md = _absolute(args.report_md)

    source_records = load_jsonl(args.input_file)
    records = build_surgical_records(source_records)
    audit_labels = load_audit_labels([args.audit_file]) if os.path.exists(args.audit_file) else {}
    summary = summarize_surgical_records(records, audit_labels=audit_labels)
    reference_view_calls = sum(int(record.get("view_calls", 0)) for record in source_records)
    cost = estimate_surgical_cost(
        baseline_cost=args.baseline_cost,
        reference_total_cost=args.reference_total_cost,
        reference_view_calls=reference_view_calls,
        surgical_view_calls=summary["view_call_count"],
    )
    summary.update(
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "boundary": BOUNDARY,
            "source_file": args.input_file,
            "output_file": args.output_file,
            **cost,
        }
    )
    write_jsonl(args.output_file, records)
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
