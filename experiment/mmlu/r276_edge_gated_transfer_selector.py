from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r231_tiny_diagnostic_runner import load_jsonl, normalize_label


VARIANTS = [
    "arg_baseline_fixed",
    "plain_requery",
    "node_only_no_promptedge_text",
    "proposed_promptnode_promptedge",
]
VALID_LABELS = {"A", "B", "C", "D", "E"}


def build_task_variant_lookup(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    tasks: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        task_id = str(row.get("task_id") or "")
        variant = str(row.get("control_variant") or "")
        if task_id and variant:
            tasks[task_id][variant] = row
    return dict(tasks)


def option_binding_surface(question: str) -> bool:
    text = str(question or "").lower()
    option_lines = [line for line in text.splitlines() if line.strip().startswith("option ")]
    option_text = "\n".join(option_lines)
    has_expression = bool(re.search(r"[\d][\d\s().,+\-*/×÷=]+", option_text))
    wording = any(term in text for term in ["expression", "equation", "formula", "which of the following", "represents"])
    return has_expression and wording


def _label(row: Dict[str, Any], key: str = "predicted_answer") -> str:
    return normalize_label(row.get(key))


def _base_record(task_id: str, task: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    first = next(iter(task.values()))
    arg = task.get("arg_baseline_fixed", {})
    true_answer = _label(first, "true_answer")
    arg_prediction = _label(arg or first, "arg_prediction") or _label(arg)
    if arg_prediction == "NONE":
        arg_prediction = _label(first, "arg_prediction")
    return {
        "run_id": "R276",
        "task_id": task_id,
        "selection_role": first.get("selection_role"),
        "subject": first.get("model_visible_input", {}).get("subject"),
        "true_answer": true_answer,
        "arg_prediction": arg_prediction,
        "arg_is_correct": arg_prediction == true_answer if true_answer in VALID_LABELS else None,
        "question": first.get("model_visible_input", {}).get("question", ""),
        "view_predictions": {
            "arg": arg_prediction,
            "plain": _label(task.get("plain_requery", {})),
            "node_only": _label(task.get("node_only_no_promptedge_text", {})),
            "promptedge": _label(task.get("proposed_promptnode_promptedge", {})),
        },
    }


def apply_edge_gated_selector(task_id: str, task: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    record = _base_record(task_id, task)
    views = record["view_predictions"]
    arg = views["arg"]
    plain = views["plain"]
    node = views["node_only"]
    edge = views["promptedge"]
    non_arg_labels = [label for label in [plain, node, edge] if label in VALID_LABELS and label != arg]
    counts = Counter(non_arg_labels)
    lifecycle_actions: List[str] = []

    if plain == node == edge and plain in VALID_LABELS and plain != arg:
        predicted = plain
        rule = "switch_unanimous_api_views"
        lifecycle_actions = ["merge", "forward", "upgrade"]
    elif plain == node and plain in VALID_LABELS and plain != arg:
        predicted = plain
        rule = "switch_plain_node_agree_prune_promptedge"
        lifecycle_actions = ["prune", "merge", "forward"]
    elif node == edge and node in VALID_LABELS and node != arg and plain == arg and option_binding_surface(record["question"]):
        predicted = node
        rule = "switch_graph_family_option_binding"
        lifecycle_actions = ["write", "merge", "forward"]
    elif counts and counts.most_common(1)[0][1] >= 2:
        predicted = arg
        rule = "keep_arg_unresolved_view_conflict"
        lifecycle_actions = ["compress", "prune"]
    else:
        predicted = arg
        rule = "keep_arg_no_safe_switch"
        lifecycle_actions = ["compress"]

    true_answer = record["true_answer"]
    is_correct = predicted == true_answer if true_answer in VALID_LABELS else None
    record.update(
        {
            "predicted_answer": predicted,
            "is_correct": is_correct,
            "fix": record["arg_is_correct"] is False and is_correct is True,
            "harm": record["arg_is_correct"] is True and is_correct is False,
            "decision_rule": rule,
            "promptnode_roles": ["PN_Memory", "PN_InstructionVerifier", "PN_Router"],
            "edge_permissions": ["read", "write", "forward"],
            "lifecycle_actions": lifecycle_actions,
            "model_visible_features_only": True,
            "claim_boundary": "Offline selector replay over existing API views; not a trained model or fresh held-out transfer claim.",
        }
    )
    return record


def _variant_correct(rows: List[Dict[str, Any]], variant: str) -> int:
    return sum(1 for row in rows if row.get("control_variant") == variant and row.get("is_correct"))


def summarize_selector_records(
    records: List[Dict[str, Any]],
    baseline_correct: int,
    plain_correct: int,
    node_correct: int,
    proposed_correct: int,
) -> Dict[str, Any]:
    total = len(records)
    correct = sum(1 for row in records if row.get("is_correct"))
    fixes = sum(1 for row in records if row.get("fix"))
    harms = sum(1 for row in records if row.get("harm"))
    return {
        "run_id": "R276",
        "title": "Edge-gated transfer selector replay",
        "claim_boundary": "Offline selector replay over existing full24 API views; supports redesign only until prospectively validated.",
        "records": total,
        "correct": correct,
        "accuracy": correct / total if total else None,
        "fixes": fixes,
        "harms": harms,
        "fix_harm": f"{fixes}/{harms}",
        "arg_baseline_correct": baseline_correct,
        "plain_requery_correct": plain_correct,
        "node_only_correct": node_correct,
        "proposed_promptnode_promptedge_correct": proposed_correct,
        "beats_arg": correct > baseline_correct,
        "beats_plain_requery": correct > plain_correct,
        "beats_node_only": correct > node_correct,
        "beats_proposed": correct > proposed_correct,
        "no_harm": harms == 0,
        "decision_rule_counts": dict(sorted(Counter(row.get("decision_rule") for row in records).items())),
        "lifecycle_action_counts": dict(sorted(Counter(action for row in records for action in row.get("lifecycle_actions", [])).items())),
        "model_visible_features_only": all(row.get("model_visible_features_only") for row in records),
    }


def run(
    results_jsonl: str = "experiment/mmlu/run_logs/mmlu_r274_full24_transfer_api_results.jsonl",
    output_jsonl: str = "experiment/mmlu/run_logs/mmlu_r276_edge_gated_transfer_selector_results.jsonl",
    summary_json: str = "experiment/mmlu/res_logs/mmlu_r276_edge_gated_transfer_selector_summary.json",
    report_md: str = "experiment/mmlu/run_logs/mmlu_r276_edge_gated_transfer_selector_report.md",
) -> Dict[str, Any]:
    rows = load_jsonl(results_jsonl)
    tasks = build_task_variant_lookup(rows)
    records = [
        apply_edge_gated_selector(task_id, task)
        for task_id, task in sorted(tasks.items())
        if all(variant in task for variant in VARIANTS)
    ]
    summary = summarize_selector_records(
        records,
        baseline_correct=_variant_correct(rows, "arg_baseline_fixed"),
        plain_correct=_variant_correct(rows, "plain_requery"),
        node_correct=_variant_correct(rows, "node_only_no_promptedge_text"),
        proposed_correct=_variant_correct(rows, "proposed_promptnode_promptedge"),
    )
    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R276 Edge-Gated Transfer Selector Replay",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Correct: `{summary['correct']}` / `{summary['records']}`",
            f"- Fix/Harm: `{summary['fix_harm']}`",
            f"- ARG/plain/node/proposed: `{summary['arg_baseline_correct']}` / `{summary['plain_requery_correct']}` / `{summary['node_only_correct']}` / `{summary['proposed_promptnode_promptedge_correct']}`",
            f"- Beats ARG/plain/node/proposed: `{summary['beats_arg']}` / `{summary['beats_plain_requery']}` / `{summary['beats_node_only']}` / `{summary['beats_proposed']}`",
            f"- Decision rules: `{summary['decision_rule_counts']}`",
            f"- Lifecycle actions: `{summary['lifecycle_action_counts']}`",
            "",
            "Interpretation: the selector treats PromptEdge text as a gated edge, not an always-on instruction. This is a redesign signal and must be validated prospectively before a paper claim.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay R276 edge-gated transfer selector.")
    parser.add_argument("--results_jsonl", default="experiment/mmlu/run_logs/mmlu_r274_full24_transfer_api_results.jsonl")
    parser.add_argument("--output_jsonl", default="experiment/mmlu/run_logs/mmlu_r276_edge_gated_transfer_selector_results.jsonl")
    parser.add_argument("--summary_json", default="experiment/mmlu/res_logs/mmlu_r276_edge_gated_transfer_selector_summary.json")
    parser.add_argument("--report_md", default="experiment/mmlu/run_logs/mmlu_r276_edge_gated_transfer_selector_report.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
