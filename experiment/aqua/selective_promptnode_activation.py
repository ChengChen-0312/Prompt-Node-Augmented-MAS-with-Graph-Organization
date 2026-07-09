import argparse
import json
import os
import re
import sys
from collections import Counter
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


RULE_NAME = "r061_selective_promptnode_activation"


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _output_text(output: Dict[str, Any]) -> str:
    raw_outputs = output.get("outputs") or []
    if isinstance(raw_outputs, str):
        return raw_outputs
    return "\n".join(str(item) for item in raw_outputs)


def extract_answer_option(text: str) -> Optional[str]:
    """Return the last explicit A-E answer option in a text block."""

    patterns = [
        r"\bthe\s+answer\s+is\s*[:\-]?\s*([A-E])\b",
        r"\banswer\s*(?:is|:)\s*([A-E])\b",
    ]
    matches: List[str] = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text or "", flags=re.I))
    if not matches:
        return None
    return normalize_option(matches[-1])


def extract_direct_votes(record: Dict[str, Any]) -> List[str]:
    votes = []
    for output in record.get("agent_outputs") or []:
        role = str(output.get("role", ""))
        if role.startswith("PN_"):
            continue
        option = extract_answer_option(_output_text(output))
        if option in VALID_OPTIONS:
            votes.append(option)
    return votes


def summarize_direct_votes(votes: Iterable[str]) -> Dict[str, Any]:
    valid_votes = [vote for vote in votes if vote in VALID_OPTIONS]
    counts = Counter(valid_votes)
    max_count = max(counts.values()) if counts else 0
    return {
        "direct_votes": valid_votes,
        "direct_vote_counts": dict(sorted(counts.items())),
        "direct_distinct_options": sorted(counts),
        "direct_distinct_count": len(counts),
        "direct_valid_vote_count": len(valid_votes),
        "direct_max_count": max_count,
    }


def should_activate_promptnode(
    baseline_record: Dict[str, Any],
    promptnode_record: Dict[str, Any],
    min_distinct_options: int = 2,
    direct_majority_threshold: int = 2,
    strong_statuses: Optional[set[str]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    strong_statuses = strong_statuses or set(STRONG_BINDING_STATUS)
    direct_summary = summarize_direct_votes(extract_direct_votes(baseline_record))
    contract_features = extract_contract_consensus_features(promptnode_record)

    baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
    promptnode_prediction = normalize_option(promptnode_record.get("predicted_answer"))
    router_option = normalize_option(contract_features.get("router_option"))
    router_status = str(contract_features.get("router_binding_status") or "").upper()
    direct_options = set(direct_summary["direct_distinct_options"])

    features: Dict[str, Any] = {
        "rule": RULE_NAME,
        "baseline_prediction": baseline_prediction,
        "promptnode_prediction": promptnode_prediction,
        **direct_summary,
        "router_option": router_option,
        "router_binding_status": router_status,
        "router_contract_count": contract_features.get("router_contract_count", 0),
        "strong_router_contract_count": contract_features.get("strong_router_contract_count", 0),
        "router_option_in_direct_votes": router_option in direct_options,
        "promptnode_prediction_valid": promptnode_prediction in VALID_OPTIONS,
        "baseline_prediction_valid": baseline_prediction in VALID_OPTIONS,
    }

    block_reason = ""
    if direct_summary["direct_distinct_count"] < min_distinct_options:
        block_reason = "direct_not_conflicted"
    elif direct_summary["direct_max_count"] >= direct_majority_threshold:
        block_reason = "direct_majority"
    elif router_option not in VALID_OPTIONS or router_status not in strong_statuses:
        block_reason = "no_strong_router_contract"
    elif router_option not in direct_options:
        block_reason = "router_not_in_direct_votes"
    elif promptnode_prediction not in VALID_OPTIONS:
        block_reason = "invalid_promptnode_prediction"

    activate = block_reason == ""
    features["activate_promptnode"] = activate
    features["block_reason"] = "" if activate else block_reason
    return activate, features


def _common_task_ids(
    baseline_records: Dict[str, Dict[str, Any]],
    promptnode_records: Dict[str, Dict[str, Any]],
) -> List[str]:
    return [task_id for task_id in baseline_records if task_id in promptnode_records]


def build_selective_records(
    baseline_records: Dict[str, Dict[str, Any]],
    promptnode_records: Dict[str, Dict[str, Any]],
    task_ids: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    selected_records = []
    selected_task_ids = list(task_ids) if task_ids is not None else _common_task_ids(
        baseline_records,
        promptnode_records,
    )

    for task_id in selected_task_ids:
        baseline_record = baseline_records[task_id]
        promptnode_record = promptnode_records[task_id]
        activate, gate_features = should_activate_promptnode(baseline_record, promptnode_record)

        baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
        promptnode_prediction = normalize_option(promptnode_record.get("predicted_answer"))
        selected_source = "promptnode" if activate else "baseline"
        selected_prediction = promptnode_prediction if activate else baseline_prediction
        true_answer = normalize_option(
            baseline_record.get("true_answer") or promptnode_record.get("true_answer")
        )

        selected_records.append(
            {
                "task_id": task_id,
                "question": baseline_record.get("question") or promptnode_record.get("question"),
                "true_answer": true_answer,
                "predicted_answer": selected_prediction,
                "is_solved": selected_prediction == true_answer,
                "selected_source": selected_source,
                "baseline_prediction": baseline_prediction,
                "promptnode_prediction": promptnode_prediction,
                "baseline_is_solved": baseline_prediction == true_answer,
                "promptnode_is_solved": promptnode_prediction == true_answer,
                "selection_rule": RULE_NAME,
                "gate_features": gate_features,
            }
        )
    return selected_records


def summarize_selected_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    solved = sum(1 for record in records if record.get("is_solved"))
    baseline_solved = sum(1 for record in records if record.get("baseline_is_solved"))
    promptnode_solved = sum(1 for record in records if record.get("promptnode_is_solved"))
    switch_records = [record for record in records if record.get("selected_source") == "promptnode"]
    fix_records = [
        record
        for record in records
        if not record.get("baseline_is_solved") and record.get("is_solved")
    ]
    harm_records = [
        record
        for record in records
        if record.get("baseline_is_solved") and not record.get("is_solved")
    ]

    return {
        "rule": RULE_NAME,
        "total_tasks": total,
        "solved_tasks": solved,
        "accuracy": solved / total if total else 0.0,
        "pass_at_1": solved / total * 100 if total else 0.0,
        "baseline_solved_tasks": baseline_solved,
        "baseline_accuracy": baseline_solved / total if total else 0.0,
        "baseline_pass_at_1": baseline_solved / total * 100 if total else 0.0,
        "promptnode_solved_tasks": promptnode_solved,
        "promptnode_accuracy": promptnode_solved / total if total else 0.0,
        "promptnode_pass_at_1": promptnode_solved / total * 100 if total else 0.0,
        "delta_vs_baseline": solved - baseline_solved,
        "delta_vs_promptnode": solved - promptnode_solved,
        "selected_promptnode_count": len(switch_records),
        "switch_tasks": [record["task_id"] for record in switch_records],
        "fixes_vs_baseline": len(fix_records),
        "harms_vs_baseline": len(harm_records),
        "fix_tasks": [record["task_id"] for record in fix_records],
        "harm_tasks": [record["task_id"] for record in harm_records],
    }


def write_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json(path: str, payload: Dict[str, Any]) -> None:
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def render_report(
    split_name: str,
    baseline_file: str,
    promptnode_file: str,
    summary: Dict[str, Any],
    records: List[Dict[str, Any]],
) -> str:
    switched_records = [record for record in records if record["selected_source"] == "promptnode"]
    switch_lines = []
    for record in switched_records:
        gate = record["gate_features"]
        switch_lines.append(
            "| {task_id} | {base} | {pn} | {selected} | {router} | {status} | {solved} |".format(
                task_id=record["task_id"],
                base=record.get("baseline_prediction"),
                pn=record.get("promptnode_prediction"),
                selected=record.get("predicted_answer"),
                router=gate.get("router_option"),
                status=gate.get("router_binding_status"),
                solved=record.get("is_solved"),
            )
        )
    if not switch_lines:
        switch_lines.append("| none | - | - | - | - | - | - |")

    return "\n".join(
        [
            f"# R061 Selective PromptNode Activation Report: {split_name}",
            "",
            "## Boundary",
            "",
            "This is a label-free replay over existing ARG and R058 traces. It is not a fresh integrated API run.",
            "The activation gate does not read `true_answer`, `is_solved`, task ids, or clean/noisy audit labels.",
            "",
            "## Inputs",
            "",
            f"- Baseline file: `{baseline_file}`",
            f"- PromptNode file: `{promptnode_file}`",
            "",
            "## Summary",
            "",
            f"- Selected accuracy: `{summary['solved_tasks']}/{summary['total_tasks']}` "
            f"= `{summary['pass_at_1']:.2f}%`",
            f"- ARG baseline accuracy: `{summary['baseline_solved_tasks']}/{summary['total_tasks']}` "
            f"= `{summary['baseline_pass_at_1']:.2f}%`",
            f"- R058 PromptNode accuracy if dense: `{summary['promptnode_solved_tasks']}/{summary['total_tasks']}` "
            f"= `{summary['promptnode_pass_at_1']:.2f}%`",
            f"- Delta vs baseline: `{summary['delta_vs_baseline']}`",
            f"- Fix/harm vs baseline: `{summary['fixes_vs_baseline']}/{summary['harms_vs_baseline']}`",
            f"- PromptNode switches: `{summary['selected_promptnode_count']}`",
            "",
            "## Switched Tasks",
            "",
            "| task_id | baseline | promptnode | selected | router | binding | solved |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *switch_lines,
            "",
            "## Claim Boundary",
            "",
            "R061 may support a selective-activation hypothesis only as replay evidence. "
            "A paper-level system claim still requires a fresh integrated evaluator that runs the same model setting "
            "and activates PromptNodes online under this gate.",
            "",
        ]
    )


def run_replay(args: argparse.Namespace) -> Dict[str, Any]:
    baseline_records = load_jsonl_by_task(args.baseline_file)
    promptnode_records = load_jsonl_by_task(args.promptnode_file)
    records = build_selective_records(baseline_records, promptnode_records)
    summary = summarize_selected_records(records)
    summary.update(
        {
            "split_name": args.split_name,
            "baseline_file": args.baseline_file,
            "promptnode_file": args.promptnode_file,
            "output_file": args.output_file,
            "summary_json": args.summary_json,
            "report_md": args.report_md,
            "boundary": "replay_over_existing_traces_not_fresh_integrated_api_run",
        }
    )

    write_jsonl(args.output_file, records)
    write_json(args.summary_json, summary)
    _ensure_parent_dir(args.report_md)
    with open(args.report_md, "w", encoding="utf-8") as f:
        f.write(render_report(args.split_name, args.baseline_file, args.promptnode_file, summary, records))
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay a label-free selective PromptNode activation gate over AQuA traces."
    )
    parser.add_argument("--split-name", required=True)
    parser.add_argument("--baseline-file", required=True)
    parser.add_argument("--promptnode-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--report-md", required=True)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = run_replay(args)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
