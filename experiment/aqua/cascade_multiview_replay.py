import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AQUA_DIR = os.path.dirname(__file__)
for path in (REPO_ROOT, AQUA_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from experiment.aqua.contract_ablation_analysis import (  # noqa: E402
    load_audit_labels,
    summarize_variant_records,
)
from experiment.aqua.contract_graph_objective import (  # noqa: E402
    select_objective_guided_prediction,
)
from experiment.aqua.evaluate_selective_multiview_promptnode import (  # noqa: E402
    rank_runtime_variants,
)
from experiment.aqua.offline_utility_selector import normalize_option  # noqa: E402
from experiment.aqua.selective_multiview_trigger import (  # noqa: E402
    ratio_text,
    write_json,
    write_jsonl,
    write_text,
)


RULE_NAME = "r071_cascade_multiview_over_r069_fresh_traces"
CLAIM_BOUNDARY = "cascade_replay_over_r069_fresh_traces_not_new_api_run"
DEFAULT_CASCADE_ORDER = ["router", "conservative", "calibrated", "candidate"]
VALID_OPTIONS = {"A", "B", "C", "D", "E"}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_json_or_jsonl(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return {}
    if path.endswith(".jsonl"):
        return json.loads(text.splitlines()[0])
    return json.loads(text)


def _option_counts(predictions: Iterable[Any]) -> Counter:
    return Counter(
        option
        for option in (normalize_option(prediction) for prediction in predictions)
        if option in VALID_OPTIONS
    )


def _selected_method(
    selected_prediction: Optional[str],
    ranked_variants: List[Dict[str, Any]],
) -> Optional[str]:
    if selected_prediction not in VALID_OPTIONS:
        return None
    if not ranked_variants:
        return None
    top_score = ranked_variants[0]["score"]
    for variant in ranked_variants:
        if variant.get("score") != top_score:
            continue
        variant_option = normalize_option(variant.get("router_option")) or normalize_option(
            variant.get("predicted_answer")
        )
        if variant_option == selected_prediction:
            return variant.get("method_key")
    return ranked_variants[0].get("method_key")


def build_cascade_record(
    r069_record: Dict[str, Any],
    cascade_order: Optional[List[str]] = None,
    baseline_accept_support: int = 2,
    switch_support_valid_baseline: int = 2,
    switch_support_invalid_baseline: int = 3,
    min_views_before_decision: int = 2,
) -> Dict[str, Any]:
    cascade_order = cascade_order or DEFAULT_CASCADE_ORDER
    baseline_prediction = normalize_option(r069_record.get("baseline_prediction"))
    true_answer = normalize_option(r069_record.get("true_answer"))
    view_records = r069_record.get("view_records") or {}
    view_predictions = r069_record.get("view_predictions") or {}
    selected_prediction = baseline_prediction
    selected_source = "baseline"
    selected_method = None
    stopped_after_method = None
    seen_records: Dict[str, Dict[str, Any]] = {}
    seen_predictions: List[Optional[str]] = []
    ranked_seen: List[Dict[str, Any]] = []

    if r069_record.get("multiview_was_run"):
        for method_key in cascade_order:
            if method_key not in view_records:
                continue
            seen_records[method_key] = view_records[method_key]
            seen_predictions.append(normalize_option(view_predictions.get(method_key)))
            stopped_after_method = method_key

            if len(seen_predictions) < min_views_before_decision:
                continue

            counts = _option_counts(seen_predictions)
            if (
                baseline_prediction in VALID_OPTIONS
                and counts.get(baseline_prediction, 0) >= baseline_accept_support
            ):
                selected_prediction = baseline_prediction
                selected_source = "baseline_early_accept"
                selected_method = None
                break

            ranked_seen = rank_runtime_variants(
                seen_records,
                [method for method in cascade_order if method in seen_records],
            )
            candidate_prediction, candidate_source = select_objective_guided_prediction(
                baseline_prediction,
                ranked_seen,
                min_top_score=1,
                min_score_margin=0,
            )
            support_threshold = (
                switch_support_invalid_baseline
                if baseline_prediction is None
                else switch_support_valid_baseline
            )
            if (
                candidate_source != "baseline"
                and candidate_prediction in VALID_OPTIONS
                and counts.get(candidate_prediction, 0) >= support_threshold
            ):
                selected_prediction = candidate_prediction
                selected_source = "cascade_objective"
                selected_method = _selected_method(candidate_prediction, ranked_seen)
                break

    view_calls = len(seen_records)
    full_view_count = len(view_records) if r069_record.get("multiview_was_run") else 0
    decision_features = {
        "rule": RULE_NAME,
        "cascade_order": cascade_order,
        "baseline_prediction": baseline_prediction,
        "seen_methods": list(seen_records),
        "seen_predictions": seen_predictions,
        "view_prediction_counts": dict(_option_counts(seen_predictions)),
        "baseline_accept_support": baseline_accept_support,
        "switch_support_valid_baseline": switch_support_valid_baseline,
        "switch_support_invalid_baseline": switch_support_invalid_baseline,
        "min_views_before_decision": min_views_before_decision,
        "stopped_after_method": stopped_after_method,
    }
    return {
        "task_id": r069_record.get("task_id"),
        "question": r069_record.get("question"),
        "true_answer": true_answer,
        "predicted_answer": selected_prediction,
        "is_solved": selected_prediction == true_answer,
        "selected_source": selected_source,
        "selected_method": selected_method,
        "selection_rule": RULE_NAME,
        "baseline_prediction": baseline_prediction,
        "baseline_is_solved": baseline_prediction == true_answer,
        "r069_predicted_answer": normalize_option(r069_record.get("predicted_answer")),
        "r069_selected_source": r069_record.get("selected_source"),
        "r069_selected_method": r069_record.get("selected_method"),
        "multiview_was_run": bool(r069_record.get("multiview_was_run")),
        "view_calls": view_calls,
        "full_view_count": full_view_count,
        "view_predictions": {
            method: normalize_option(view_predictions.get(method))
            for method in cascade_order
            if method in view_predictions
        },
        "ranked_seen_variants": ranked_seen,
        "decision_features": decision_features,
    }


def summarize_cascade_records(
    records: List[Dict[str, Any]],
    audit_labels: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    audit_labels = audit_labels or {}
    total = len(records)
    solved = sum(1 for record in records if record.get("is_solved"))
    baseline = sum(1 for record in records if record.get("baseline_is_solved"))
    run_records = [record for record in records if record.get("multiview_was_run")]
    switch_records = [record for record in records if record.get("selected_source") == "cascade_objective"]
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
    posthoc = summarize_variant_records(RULE_NAME, records, audit_labels) if audit_labels else {}
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "total_tasks": total,
        "solved_tasks": solved,
        "baseline_solved_tasks": baseline,
        "overall": ratio_text(solved, total),
        "baseline": ratio_text(baseline, total),
        "delta_vs_baseline": solved - baseline,
        "multiview_run_count": len(run_records),
        "multiview_run": ratio_text(len(run_records), total),
        "cascade_view_calls": sum(int(record.get("view_calls", 0)) for record in records),
        "full_view_calls": sum(int(record.get("full_view_count", 0)) for record in records),
        "switches": len(switch_records),
        "switch_tasks": [record["task_id"] for record in switch_records],
        "fixes": len(fixes),
        "harms": len(harms),
        "fix_harm": f"{len(fixes)}/{len(harms)}",
        "fix_tasks": [record["task_id"] for record in fixes],
        "harm_tasks": [record["task_id"] for record in harms],
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


def estimate_cascade_cost(
    summary: Dict[str, Any],
    r069_summary: Dict[str, Any],
    baseline_summary: Dict[str, Any],
) -> Dict[str, Any]:
    baseline_cost = float(baseline_summary.get("cost", 0.0))
    r069_cost = float(r069_summary.get("cost", 0.0))
    full_view_calls = int(summary.get("full_view_calls", 0))
    cascade_view_calls = int(summary.get("cascade_view_calls", 0))
    view_fraction = cascade_view_calls / full_view_calls if full_view_calls else 0.0
    view_cost = max(r069_cost - baseline_cost, 0.0)
    estimated_cost = baseline_cost + view_cost * view_fraction
    return {
        "cost_model": "historical_arg_baseline_cost_plus_r069_view_cost_scaled_by_cascade_view_calls",
        "baseline_cost": baseline_cost,
        "r069_full_integrated_cost": r069_cost,
        "r069_estimated_view_cost": view_cost,
        "full_view_calls": full_view_calls,
        "cascade_view_calls": cascade_view_calls,
        "view_call_fraction": view_fraction,
        "view_call_reduction": 1.0 - view_fraction if full_view_calls else 0.0,
        "estimated_cost": estimated_cost,
        "estimated_cost_saving_vs_r069": r069_cost - estimated_cost,
        "relative_cost_vs_r069": estimated_cost / r069_cost if r069_cost else None,
        "relative_cost_vs_arg": estimated_cost / baseline_cost if baseline_cost else None,
    }


def build_r071_payload(base_dir: str = "experiment/aqua") -> Dict[str, Any]:
    r069_records_path = os.path.join(base_dir, "aqua_tail34_r069_integrated_selective_multiview_results.jsonl")
    r069_summary_path = os.path.join(
        base_dir,
        "res_logs",
        "aqua_tail34_r069_integrated_selective_multiview_summary.json",
    )
    baseline_summary_path = os.path.join(
        base_dir,
        "res_logs",
        "aqua_tail34_arg_baseline_summary.jsonl",
    )
    audit_path = os.path.join(base_dir, "aqua_tail34_option_binding_audit.jsonl")
    records = [build_cascade_record(record) for record in load_jsonl(r069_records_path)]
    audit_labels = load_audit_labels([audit_path]) if os.path.exists(audit_path) else {}
    summary = summarize_cascade_records(records, audit_labels=audit_labels)
    cost_estimate = estimate_cascade_cost(
        summary,
        load_json_or_jsonl(r069_summary_path),
        load_json_or_jsonl(baseline_summary_path),
    )
    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "r069_records_path": r069_records_path,
        "cascade_order": DEFAULT_CASCADE_ORDER,
        "records": records,
        "summary": summary,
        "cost_estimate": cost_estimate,
        "trigger_excludes": [
            "true_answer",
            "is_solved",
            "clean_label",
            "audit_label",
            "task_id-specific rules",
        ],
        "interpretation": (
            "Replay estimate over R069 fresh traces: run views sequentially, early-accept a valid ARG "
            "baseline after two supporting views, and switch only when the objective selector plus view "
            "support threshold is satisfied."
        ),
    }


def render_report(payload: Dict[str, Any]) -> str:
    summary = payload["summary"]
    cost = payload["cost_estimate"]
    return "\n".join(
        [
            "# R071 Cascade Multi-View Replay over R069 Fresh Traces",
            "",
            f"**Boundary**: `{payload['claim_boundary']}`. No new API calls.",
            "",
            "## Summary",
            "",
            f"- Accuracy: `{summary['overall']}`",
            f"- Internal ARG baseline: `{summary['baseline']}`",
            f"- Fix/Harm: `{summary['fix_harm']}`",
            f"- Clean: `{summary.get('clean', 'n/a')}`",
            f"- Clean Fix/Harm: `{summary.get('clean_fix_harm', 'n/a')}`",
            f"- Multi-view triggered tasks: `{summary['multiview_run']}`",
            f"- Cascade view calls: `{summary['cascade_view_calls']}/{summary['full_view_calls']}`",
            f"- Switches: `{summary['switches']}` (`{', '.join(summary['switch_tasks'])}`)",
            f"- Estimated cost: `${cost['estimated_cost']:.6f}`",
            f"- Estimated cost saving vs R069: `${cost['estimated_cost_saving_vs_r069']:.6f}`",
            f"- View-call reduction: `{cost['view_call_reduction'] * 100:.1f}%`",
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "This preserves R069/R070 accuracy in replay while cutting PromptNode view calls. It is a cost model over existing traces, not a new integrated API result.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a cascade multi-view selector over R069 fresh traces.")
    parser.add_argument("--base-dir", default=os.path.dirname(__file__))
    parser.add_argument(
        "--output-jsonl",
        default=os.path.join(os.path.dirname(__file__), "aqua_tail34_r071_cascade_multiview_results.jsonl"),
    )
    parser.add_argument(
        "--summary-json",
        default=os.path.join(os.path.dirname(__file__), "res_logs/aqua_tail34_r071_cascade_multiview_summary.json"),
    )
    parser.add_argument(
        "--report-md",
        default=os.path.join(os.path.dirname(__file__), "run_logs/aqua_tail34_r071_cascade_multiview_report.md"),
    )
    args = parser.parse_args()
    payload = build_r071_payload(args.base_dir)
    write_jsonl(args.output_jsonl, payload["records"])
    output_payload = {key: value for key, value in payload.items() if key != "records"}
    output_payload["output_jsonl"] = args.output_jsonl
    write_json(args.summary_json, output_payload)
    write_text(args.report_md, render_report(payload))
    print(
        "R071 cascade replay: "
        f"overall={payload['summary']['overall']} baseline={payload['summary']['baseline']} "
        f"view_calls={payload['summary']['cascade_view_calls']}/{payload['summary']['full_view_calls']} "
        f"cost=${payload['cost_estimate']['estimated_cost']:.6f}"
    )


if __name__ == "__main__":
    main()
