import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.offline_utility_selector import (  # noqa: E402
    STRONG_BINDING_STATUS,
    VALID_OPTIONS,
    extract_contract_consensus_features,
    load_jsonl_by_task,
    normalize_option,
)
from experiment.aqua.selective_promptnode_activation import (  # noqa: E402
    extract_direct_votes,
    summarize_direct_votes,
    write_json,
    write_jsonl,
)


RULE_NAME = "r063_risk_aware_promptnode_activation"


def _non_promptnode_output_count(record: Dict[str, Any]) -> int:
    return sum(
        1
        for output in record.get("agent_outputs") or []
        if not str(output.get("role", "")).startswith("PN_")
    )


def _baseline_source_record(record: Dict[str, Any]) -> Dict[str, Any]:
    nested = record.get("baseline_record")
    if isinstance(nested, dict):
        return nested
    return record


def extract_baseline_risk_features(record: Dict[str, Any]) -> Dict[str, Any]:
    baseline = _baseline_source_record(record)
    baseline_prediction = normalize_option(baseline.get("predicted_answer"))
    direct_summary = summarize_direct_votes(extract_direct_votes(baseline))
    non_promptnode_count = _non_promptnode_output_count(baseline)
    direct_options = set(direct_summary["direct_distinct_options"])
    final_direct_support_count = (
        direct_summary["direct_vote_counts"].get(baseline_prediction, 0)
        if baseline_prediction in VALID_OPTIONS
        else 0
    )

    direct_conflict = (
        direct_summary["direct_distinct_count"] >= 2 and direct_summary["direct_max_count"] < 2
    )
    invalid_baseline_prediction = baseline_prediction not in VALID_OPTIONS
    final_direct_mismatch = (
        invalid_baseline_prediction or baseline_prediction not in direct_options
    )
    weak_final_support = (
        baseline_prediction in VALID_OPTIONS and final_direct_support_count < 2
    )
    missing_direct_vote_count = max(
        non_promptnode_count - direct_summary["direct_valid_vote_count"],
        0,
    )
    low_direct_coverage = direct_summary["direct_valid_vote_count"] < 2

    return {
        "rule": RULE_NAME,
        "baseline_prediction": baseline_prediction,
        **direct_summary,
        "non_promptnode_output_count": non_promptnode_count,
        "missing_direct_vote_count": missing_direct_vote_count,
        "final_direct_support_count": final_direct_support_count,
        "direct_conflict": direct_conflict,
        "final_direct_mismatch": final_direct_mismatch,
        "weak_final_support": weak_final_support,
        "missing_direct_vote": missing_direct_vote_count > 0,
        "invalid_baseline_prediction": invalid_baseline_prediction,
        "low_direct_coverage": low_direct_coverage,
    }


def should_run_promptnode_r063(features: Dict[str, Any]) -> bool:
    if features.get("direct_conflict"):
        return True
    if features.get("invalid_baseline_prediction"):
        return True
    if features.get("final_direct_mismatch"):
        return True
    if features.get("low_direct_coverage") and features.get("weak_final_support"):
        return True
    return False


def should_select_promptnode_r063(
    baseline_record: Dict[str, Any],
    promptnode_record: Dict[str, Any],
    risk_features: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    contract_features = extract_contract_consensus_features(promptnode_record)
    baseline_prediction = normalize_option(
        _baseline_source_record(baseline_record).get("predicted_answer")
    )
    promptnode_prediction = normalize_option(promptnode_record.get("predicted_answer"))
    router_option = normalize_option(contract_features.get("router_option"))
    router_status = str(contract_features.get("router_binding_status") or "").upper()
    direct_options = set(risk_features.get("direct_distinct_options") or [])

    features = {
        **risk_features,
        "baseline_prediction": baseline_prediction,
        "promptnode_prediction": promptnode_prediction,
        "router_option": router_option,
        "router_binding_status": router_status,
        "router_contract_count": contract_features.get("router_contract_count", 0),
        "strong_router_contract_count": contract_features.get("strong_router_contract_count", 0),
        "router_option_in_direct_votes": router_option in direct_options,
        "promptnode_prediction_valid": promptnode_prediction in VALID_OPTIONS,
        "baseline_prediction_valid": baseline_prediction in VALID_OPTIONS,
    }

    selection_reason = ""
    block_reason = ""
    if promptnode_prediction not in VALID_OPTIONS:
        block_reason = "invalid_promptnode_prediction"
    elif router_option not in VALID_OPTIONS or router_status not in STRONG_BINDING_STATUS:
        block_reason = "no_strong_router_contract"
    elif promptnode_prediction != router_option:
        block_reason = "promptnode_prediction_not_router_option"
    elif risk_features.get("direct_conflict") and router_option in direct_options:
        selection_reason = "strong_router_resolves_conflict"
    elif risk_features.get("invalid_baseline_prediction") and router_option in VALID_OPTIONS:
        selection_reason = "strong_router_replaces_invalid_baseline"
    elif risk_features.get("final_direct_mismatch") and not direct_options:
        selection_reason = "strong_router_replaces_unsupported_final_without_direct_votes"
    else:
        block_reason = "router_not_compatible"

    selected = bool(selection_reason)
    features["select_promptnode"] = selected
    features["selection_reason"] = selection_reason
    features["selection_block_reason"] = "" if selected else block_reason
    return selected, features


def build_r063_replay_records(
    baseline_records: Dict[str, Dict[str, Any]],
    promptnode_records: Dict[str, Dict[str, Any]],
    task_ids: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    selected_records = []
    selected_task_ids = list(task_ids) if task_ids is not None else [
        task_id for task_id in baseline_records if task_id in promptnode_records
    ]

    for task_id in selected_task_ids:
        original_baseline_record = baseline_records[task_id]
        baseline_record = _baseline_source_record(original_baseline_record)
        promptnode_record = promptnode_records[task_id]
        risk_features = extract_baseline_risk_features(original_baseline_record)
        promptnode_would_run = should_run_promptnode_r063(risk_features)

        if promptnode_would_run:
            select_promptnode, gate_features = should_select_promptnode_r063(
                original_baseline_record,
                promptnode_record,
                risk_features,
            )
        else:
            select_promptnode = False
            gate_features = {
                **risk_features,
                "select_promptnode": False,
                "selection_reason": "",
                "selection_block_reason": "risk_prefilter_blocked",
            }

        baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
        promptnode_prediction = normalize_option(promptnode_record.get("predicted_answer"))
        selected_source = "promptnode" if select_promptnode else "baseline"
        selected_prediction = promptnode_prediction if select_promptnode else baseline_prediction
        true_answer = normalize_option(
            baseline_record.get("true_answer")
            or original_baseline_record.get("true_answer")
            or promptnode_record.get("true_answer")
        )

        selected_records.append(
            {
                "task_id": task_id,
                "question": baseline_record.get("question") or promptnode_record.get("question"),
                "true_answer": true_answer,
                "predicted_answer": selected_prediction,
                "is_solved": selected_prediction == true_answer,
                "selected_source": selected_source,
                "promptnode_would_run": promptnode_would_run,
                "baseline_prediction": baseline_prediction,
                "promptnode_prediction": promptnode_prediction,
                "baseline_is_solved": baseline_prediction == true_answer,
                "promptnode_is_solved": promptnode_prediction == true_answer,
                "risk_features": risk_features,
                "gate_features": gate_features,
                "selection_rule": RULE_NAME,
            }
        )
    return selected_records


def summarize_r063_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    solved = sum(1 for record in records if record.get("is_solved"))
    baseline_solved = sum(1 for record in records if record.get("baseline_is_solved"))
    promptnode_solved = sum(1 for record in records if record.get("promptnode_is_solved"))
    run_records = [record for record in records if record.get("promptnode_would_run")]
    switch_records = [record for record in records if record.get("selected_source") == "promptnode"]
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

    return {
        "rule": RULE_NAME,
        "total_tasks": total,
        "solved_tasks": solved,
        "pass_at_1": solved / total * 100 if total else 0.0,
        "baseline_solved_tasks": baseline_solved,
        "baseline_pass_at_1": baseline_solved / total * 100 if total else 0.0,
        "dense_promptnode_solved_tasks": promptnode_solved,
        "dense_promptnode_pass_at_1": promptnode_solved / total * 100 if total else 0.0,
        "delta_vs_baseline": solved - baseline_solved,
        "promptnode_run_count": len(run_records),
        "promptnode_switch_count": len(switch_records),
        "fixes_vs_baseline": len(fixes),
        "harms_vs_baseline": len(harms),
        "promptnode_run_tasks": [record["task_id"] for record in run_records],
        "switch_tasks": [record["task_id"] for record in switch_records],
        "fix_tasks": [record["task_id"] for record in fixes],
        "harm_tasks": [record["task_id"] for record in harms],
    }


def render_report(
    split_name: str,
    baseline_file: str,
    promptnode_file: str,
    summary: Dict[str, Any],
    records: List[Dict[str, Any]],
) -> str:
    run_lines = []
    for record in records:
        if not record.get("promptnode_would_run"):
            continue
        gate = record.get("gate_features", {})
        risk = record.get("risk_features", {})
        run_lines.append(
            "| {task} | {base} | {pn} | {selected} | {run} | {reason} | {block} | {solved} |".format(
                task=record["task_id"],
                base=record.get("baseline_prediction"),
                pn=record.get("promptnode_prediction"),
                selected=record.get("selected_source"),
                run=",".join(
                    key
                    for key in (
                        "direct_conflict",
                        "final_direct_mismatch",
                        "invalid_baseline_prediction",
                        "low_direct_coverage",
                    )
                    if risk.get(key)
                ),
                reason=gate.get("selection_reason", ""),
                block=gate.get("selection_block_reason", ""),
                solved=record.get("is_solved"),
            )
        )
    if not run_lines:
        run_lines.append("| none | - | - | - | - | - | - | - |")

    return "\n".join(
        [
            f"# R063 Risk-Aware PromptNode Replay Report: {split_name}",
            "",
            "## Boundary",
            "",
            "This is an exploratory replay over existing R062 baseline records and dense R060 PromptNode traces.",
            "The risk features and gate do not read `true_answer`, `is_solved`, task ids, or clean/noisy labels.",
            "Because tail34 has already informed R063 design, this cannot be treated as a fresh held-out accuracy claim.",
            "",
            "## Inputs",
            "",
            f"- Baseline file: `{baseline_file}`",
            f"- Dense PromptNode file: `{promptnode_file}`",
            "",
            "## Summary",
            "",
            f"- Selected accuracy: `{summary['solved_tasks']}/{summary['total_tasks']}` = `{summary['pass_at_1']:.2f}%`",
            f"- Baseline accuracy: `{summary['baseline_solved_tasks']}/{summary['total_tasks']}` = `{summary['baseline_pass_at_1']:.2f}%`",
            f"- Dense PromptNode accuracy: `{summary['dense_promptnode_solved_tasks']}/{summary['total_tasks']}` = `{summary['dense_promptnode_pass_at_1']:.2f}%`",
            f"- PromptNode run count: `{summary['promptnode_run_count']}/{summary['total_tasks']}`",
            f"- PromptNode switch count: `{summary['promptnode_switch_count']}`",
            f"- Fix/harm vs baseline: `{summary['fixes_vs_baseline']}/{summary['harms_vs_baseline']}`",
            "",
            "## PromptNode Would Run",
            "",
            "| task_id | baseline | dense PN | selected | risk reasons | selection reason | block reason | solved |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *run_lines,
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay a risk-aware selective PromptNode activation rule over AQuA traces."
    )
    parser.add_argument("--split-name", required=True)
    parser.add_argument("--baseline-file", required=True)
    parser.add_argument("--promptnode-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--report-md", required=True)
    return parser


def run_replay(args: argparse.Namespace) -> Dict[str, Any]:
    baseline_records = load_jsonl_by_task(args.baseline_file)
    promptnode_records = load_jsonl_by_task(args.promptnode_file)
    records = build_r063_replay_records(baseline_records, promptnode_records)
    summary = summarize_r063_records(records)
    summary.update(
        {
            "split_name": args.split_name,
            "baseline_file": args.baseline_file,
            "promptnode_file": args.promptnode_file,
            "output_file": args.output_file,
            "summary_json": args.summary_json,
            "report_md": args.report_md,
            "boundary": "exploratory_replay_not_fresh_heldout_claim",
        }
    )
    write_jsonl(args.output_file, records)
    write_json(args.summary_json, summary)
    parent = os.path.dirname(args.report_md)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.report_md, "w", encoding="utf-8") as f:
        f.write(render_report(args.split_name, args.baseline_file, args.promptnode_file, summary, records))
    return summary


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = run_replay(args)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
