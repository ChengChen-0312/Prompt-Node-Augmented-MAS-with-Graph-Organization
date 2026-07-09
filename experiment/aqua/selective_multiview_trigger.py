import argparse
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
from experiment.aqua.offline_utility_selector import (  # noqa: E402
    VALID_OPTIONS,
    load_jsonl_by_task,
    normalize_option,
)
from experiment.aqua.risk_aware_promptnode_activation import (  # noqa: E402
    extract_baseline_risk_features,
    should_run_promptnode_r063,
)


RULE_NAME = "r068_selective_multiview_trigger"
CLAIM_BOUNDARY = "selective_multiview_replay_not_fresh_api_run"
VIEW_SUMMARY_FILES = [
    "aqua_tail34_pn_router_contract_summary.jsonl",
    "aqua_tail34_pn_candidate_select_summary.jsonl",
    "aqua_tail34_pn_conservative_router_summary.jsonl",
    "aqua_tail34_pn_calibrated_utility_summary.jsonl",
]


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


def write_json(path: str, payload: Dict[str, Any]) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, records: Iterable[Dict[str, Any]]) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def extract_multiview_trigger_features(baseline_record: Dict[str, Any]) -> Dict[str, Any]:
    features = extract_baseline_risk_features(baseline_record)
    features["r063_trigger"] = should_run_promptnode_r063(features)
    features["missing_direct_vote_trigger"] = bool(features.get("missing_direct_vote"))
    features["trigger_rule"] = RULE_NAME
    return features


def should_run_multiview(features: Dict[str, Any]) -> bool:
    return bool(features.get("r063_trigger") or features.get("missing_direct_vote_trigger"))


def solved(prediction: Any, true_answer: Any) -> bool:
    return normalize_option(prediction) == normalize_option(true_answer)


def _common_task_ids(
    baseline_records: Dict[str, Dict[str, Any]],
    selector_records: Dict[str, Dict[str, Any]],
) -> List[str]:
    return [task_id for task_id in baseline_records if task_id in selector_records]


def build_selective_multiview_records(
    baseline_records: Dict[str, Dict[str, Any]],
    selector_records: Dict[str, Dict[str, Any]],
    task_ids: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    selected = []
    selected_task_ids = list(task_ids) if task_ids is not None else _common_task_ids(
        baseline_records,
        selector_records,
    )
    for task_id in selected_task_ids:
        baseline_record = baseline_records[task_id]
        selector_record = selector_records[task_id]
        trigger_features = extract_multiview_trigger_features(baseline_record)
        multiview_would_run = should_run_multiview(trigger_features)

        baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
        objective_prediction = normalize_option(selector_record.get("predicted_answer"))
        true_answer = normalize_option(
            baseline_record.get("true_answer") or selector_record.get("true_answer")
        )
        if multiview_would_run:
            predicted_answer = objective_prediction
            selected_source = (
                selector_record.get("selected_source")
                if objective_prediction != baseline_prediction
                else "baseline"
            )
        else:
            predicted_answer = baseline_prediction
            selected_source = "baseline"

        selected.append(
            {
                "task_id": task_id,
                "question": baseline_record.get("question") or selector_record.get("question"),
                "true_answer": true_answer,
                "predicted_answer": predicted_answer,
                "is_solved": solved(predicted_answer, true_answer),
                "selected_source": selected_source,
                "multiview_would_run": multiview_would_run,
                "baseline_prediction": baseline_prediction,
                "objective_prediction": objective_prediction,
                "baseline_is_solved": solved(baseline_prediction, true_answer),
                "objective_is_solved": solved(objective_prediction, true_answer),
                "trigger_features": trigger_features,
                "selector_rule": RULE_NAME,
            }
        )
    return selected


def ratio_text(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}"


def summarize_selective_records(
    records: List[Dict[str, Any]],
    audit_labels: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    audit_labels = audit_labels or {}
    total = len(records)
    solved_count = sum(1 for record in records if record.get("is_solved"))
    baseline_count = sum(1 for record in records if record.get("baseline_is_solved"))
    objective_count = sum(1 for record in records if record.get("objective_is_solved"))
    run_records = [record for record in records if record.get("multiview_would_run")]
    switch_records = [record for record in records if record.get("selected_source") != "baseline"]
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
        "total_tasks": total,
        "solved_tasks": solved_count,
        "baseline_solved_tasks": baseline_count,
        "objective_full_solved_tasks": objective_count,
        "overall": ratio_text(solved_count, total),
        "baseline": ratio_text(baseline_count, total),
        "objective_full": ratio_text(objective_count, total),
        "delta_vs_baseline": solved_count - baseline_count,
        "fixes": len(fixes),
        "harms": len(harms),
        "fix_harm": f"{len(fixes)}/{len(harms)}",
        "multiview_run_count": len(run_records),
        "multiview_run": ratio_text(len(run_records), total),
        "switches": len(switch_records),
        "run_tasks": [record["task_id"] for record in run_records],
        "switch_tasks": [record["task_id"] for record in switch_records],
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


def estimate_selective_cost(
    baseline_summary: Dict[str, Any],
    view_summaries: List[Dict[str, Any]],
    run_count: int,
    total_tasks: int,
) -> Dict[str, Any]:
    run_fraction = run_count / total_tasks if total_tasks else 0.0
    baseline_cost = float(baseline_summary.get("cost", 0.0))
    view_cost = sum(float(summary.get("cost", 0.0)) for summary in view_summaries)
    baseline_prompt = float(baseline_summary.get("prompt_tokens", 0.0))
    baseline_completion = float(baseline_summary.get("completion_tokens", 0.0))
    view_prompt = sum(float(summary.get("prompt_tokens", 0.0)) for summary in view_summaries)
    view_completion = sum(float(summary.get("completion_tokens", 0.0)) for summary in view_summaries)
    estimated_cost = baseline_cost + view_cost * run_fraction
    full_cost = baseline_cost + view_cost
    return {
        "cost_model": "baseline_full_plus_view_summary_cost_scaled_by_trigger_fraction",
        "run_fraction": run_fraction,
        "baseline_cost": baseline_cost,
        "view_cost_if_full": view_cost,
        "estimated_cost": estimated_cost,
        "full_multiview_cost": full_cost,
        "cost_saving_vs_full_multiview": full_cost - estimated_cost,
        "relative_cost_vs_arg": estimated_cost / baseline_cost if baseline_cost else None,
        "estimated_prompt_tokens": baseline_prompt + view_prompt * run_fraction,
        "estimated_completion_tokens": baseline_completion + view_completion * run_fraction,
        "full_prompt_tokens": baseline_prompt + view_prompt,
        "full_completion_tokens": baseline_completion + view_completion,
    }


def build_tail34_selective_payload(base_dir: str = "experiment/aqua") -> Dict[str, Any]:
    baseline_file = os.path.join(base_dir, "aqua_tail34_arg_baseline_results.jsonl")
    selector_file = os.path.join(base_dir, "aqua_tail34_objective_guided_selector_results.jsonl")
    audit_file = os.path.join(base_dir, "aqua_tail34_option_binding_audit.jsonl")
    baseline_records = load_jsonl_by_task(baseline_file)
    selector_records = load_jsonl_by_task(selector_file)
    records = build_selective_multiview_records(baseline_records, selector_records)
    audit_labels = load_audit_labels([audit_file])
    summary = summarize_selective_records(records, audit_labels=audit_labels)
    baseline_summary = load_json_or_jsonl(
        os.path.join(base_dir, "res_logs", "aqua_tail34_arg_baseline_summary.jsonl")
    )
    view_summaries = [
        load_json_or_jsonl(os.path.join(base_dir, "res_logs", filename))
        for filename in VIEW_SUMMARY_FILES
    ]
    cost_estimate = estimate_selective_cost(
        baseline_summary,
        view_summaries,
        run_count=summary["multiview_run_count"],
        total_tasks=summary["total_tasks"],
    )
    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "baseline_file": baseline_file,
        "selector_file": selector_file,
        "audit_file": audit_file,
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
            "Replay estimate: run ARG for every task, trigger all four multi-view PromptNode traces only when "
            "ARG baseline traces show R063 risk or missing direct A-E vote, then apply the existing objective selector."
        ),
    }


def render_report(payload: Dict[str, Any]) -> str:
    summary = payload["summary"]
    cost = payload["cost_estimate"]
    run_lines = []
    for record in payload["records"]:
        if not record.get("multiview_would_run"):
            continue
        features = record.get("trigger_features", {})
        reasons = [
            name
            for name in ["r063_trigger", "missing_direct_vote_trigger"]
            if features.get(name)
        ]
        run_lines.append(
            "| {task} | {base} | {obj} | {selected} | {source} | {reasons} | {solved} |".format(
                task=record["task_id"],
                base=record.get("baseline_prediction"),
                obj=record.get("objective_prediction"),
                selected=record.get("predicted_answer"),
                source=record.get("selected_source"),
                reasons=",".join(reasons),
                solved=record.get("is_solved"),
            )
        )
    return "\n".join(
        [
            "# R068 Selective Multi-View PromptNode Trigger",
            "",
            f"**Claim boundary**: `{payload['claim_boundary']}`. This is a replay/cost estimate over existing tail34 traces, not a fresh API run.",
            "",
            "## Summary",
            "",
            f"- Selected accuracy: `{summary['overall']}`",
            f"- ARG baseline: `{summary['baseline']}`",
            f"- Full objective selector: `{summary['objective_full']}`",
            f"- Fix/Harm: `{summary['fix_harm']}`",
            f"- Clean: `{summary.get('clean', 'n/a')}`",
            f"- Clean Fix/Harm: `{summary.get('clean_fix_harm', 'n/a')}`",
            f"- Multi-view runs: `{summary['multiview_run']}`",
            f"- Switch tasks: `{', '.join(summary['switch_tasks'])}`",
            "",
            "## Cost Estimate",
            "",
            f"- Estimated selective cost: `${cost['estimated_cost']:.6f}`",
            f"- Full multi-view cost: `${cost['full_multiview_cost']:.6f}`",
            f"- Cost saving vs full multi-view: `${cost['cost_saving_vs_full_multiview']:.6f}`",
            f"- Relative cost vs ARG: `{cost['relative_cost_vs_arg']:.2f}x`",
            "",
            "## Triggered Tasks",
            "",
            "| Task | ARG | Objective | Selected | Source | Trigger reasons | Solved |",
            "| --- | ---: | ---: | ---: | --- | --- | --- |",
            *run_lines,
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "This keeps the R065 answer-level signal in replay while cutting the multi-view calls from `34/34` to "
            f"`{summary['multiview_run']}`. It still needs a fresh integrated run before paper claims.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay selective multi-view PromptNode triggering on tail34.")
    parser.add_argument("--base-dir", default=os.path.dirname(__file__))
    parser.add_argument(
        "--output-jsonl",
        default=os.path.join(os.path.dirname(__file__), "aqua_tail34_r068_selective_multiview_results.jsonl"),
    )
    parser.add_argument(
        "--summary-json",
        default=os.path.join(os.path.dirname(__file__), "res_logs/aqua_tail34_r068_selective_multiview_summary.json"),
    )
    parser.add_argument(
        "--report-md",
        default=os.path.join(os.path.dirname(__file__), "run_logs/aqua_tail34_r068_selective_multiview_report.md"),
    )
    args = parser.parse_args()
    payload = build_tail34_selective_payload(args.base_dir)
    write_jsonl(args.output_jsonl, payload["records"])
    output_payload = {key: value for key, value in payload.items() if key != "records"}
    output_payload["output_jsonl"] = args.output_jsonl
    write_json(args.summary_json, output_payload)
    write_text(args.report_md, render_report(payload))
    print(
        "R068 selective multi-view replay: "
        f"overall={payload['summary']['overall']} baseline={payload['summary']['baseline']} "
        f"runs={payload['summary']['multiview_run']} cost=${payload['cost_estimate']['estimated_cost']:.6f}"
    )


if __name__ == "__main__":
    main()
