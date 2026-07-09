from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r231_tiny_diagnostic_runner import load_jsonl


API_VARIANTS = [
    "plain_requery",
    "node_only_no_promptedge_text",
    "proposed_promptnode_promptedge",
]


def build_task_variant_lookup(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    tasks: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        task_id = str(row.get("task_id") or "")
        variant = str(row.get("control_variant") or "")
        if task_id and variant:
            tasks[task_id][variant] = row
    return dict(tasks)


def classify_task_delta(task: Dict[str, Dict[str, Any]]) -> List[str]:
    plain = task.get("plain_requery", {})
    node = task.get("node_only_no_promptedge_text", {})
    proposed = task.get("proposed_promptnode_promptedge", {})
    tags: List[str] = []

    if plain.get("fix") and node.get("fix") and proposed.get("fix"):
        tags.append("all_api_fix")
    if plain.get("fix") and not proposed.get("fix"):
        tags.append("plain_fix_lost_by_proposed")
    if node.get("fix") and not proposed.get("fix"):
        tags.append("node_fix_lost_by_promptedge")
    if proposed.get("fix") and not plain.get("fix"):
        tags.append("proposed_over_plain_fix")
    if proposed.get("fix") and not node.get("fix"):
        tags.append("promptedge_added_fix")
    if proposed.get("harm"):
        tags.append("proposed_control_harm")
    if node.get("harm") and proposed.get("harm"):
        tags.append("promptnode_family_control_harm")
    if plain.get("is_correct") and not node.get("is_correct") and not proposed.get("is_correct"):
        tags.append("graph_prompt_regression_vs_plain")
    if not tags:
        tags.append("no_interesting_delta")
    return sorted(set(tags))


def _case_record(task_id: str, task: Dict[str, Dict[str, Any]], tags: List[str]) -> Dict[str, Any]:
    first = next(iter(task.values()))
    variants = {}
    for variant in API_VARIANTS:
        row = task.get(variant, {})
        variants[variant] = {
            "predicted_answer": row.get("predicted_answer"),
            "is_correct": row.get("is_correct"),
            "fix": bool(row.get("fix")),
            "harm": bool(row.get("harm")),
            "raw_response_excerpt": str(row.get("raw_response") or "")[:360],
        }
    return {
        "task_id": task_id,
        "selection_role": first.get("selection_role"),
        "true_answer": first.get("true_answer"),
        "arg_prediction": first.get("arg_prediction"),
        "tags": tags,
        "variants": variants,
    }


def summarize_failure_modes(tasks: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
    mode_counts = Counter()
    cases = []
    for task_id, task in sorted(tasks.items()):
        if not all(variant in task for variant in API_VARIANTS):
            continue
        tags = classify_task_delta(task)
        mode_counts.update(tags)
        if tags != ["no_interesting_delta"]:
            cases.append(_case_record(task_id, task, tags))
    return {
        "tasks": len(tasks),
        "interesting_cases": len(cases),
        "mode_counts": dict(sorted(mode_counts.items())),
        "cases": cases,
    }


def run_failure_mechanism_analysis(
    results_jsonl: str,
    summary_json: str,
    report_md: str,
) -> Dict[str, Any]:
    rows = load_jsonl(results_jsonl)
    tasks = build_task_variant_lookup(rows)
    summary = summarize_failure_modes(tasks)
    output = {
        "run_id": "R256",
        "title": "MMLU transfer failure mechanism analysis",
        "claim_boundary": "No-API failure analysis only; supports redesign decisions, not accuracy claims.",
        "no_api": True,
        "broad_api": False,
        "results_jsonl": results_jsonl,
        **summary,
        "design_constraints_for_v2": [
            "Do not treat PromptEdge text as intrinsically beneficial; R254 shows node-only beats proposed.",
            "Add a selector gate: use PN/PE only when it improves over plain reasoning signals or preserves controls.",
            "Reduce over-conditioning on ARG initial choice and edge procedure when plain requery already solves the item.",
            "Add a harm guard for matched-control cases before switching away from ARG.",
        ],
    }
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(output))
    return output


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R256 MMLU Transfer Failure Mechanism Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Tasks: `{summary['tasks']}`",
        f"- Interesting cases: `{summary['interesting_cases']}`",
        f"- Mode counts: `{summary['mode_counts']}`",
        "",
        "## Key Cases",
        "",
    ]
    for case in summary["cases"][:8]:
        rows.extend(
            [
                f"### {case['task_id']}",
                "",
                f"- Role: `{case['selection_role']}`; ARG/true: `{case['arg_prediction']}` / `{case['true_answer']}`",
                f"- Tags: `{case['tags']}`",
                f"- Plain/node/proposed: `{case['variants']['plain_requery']['predicted_answer']}` / `{case['variants']['node_only_no_promptedge_text']['predicted_answer']}` / `{case['variants']['proposed_promptnode_promptedge']['predicted_answer']}`",
                "",
            ]
        )
    rows.extend(
        [
            "## V2 Constraints",
            "",
        ]
    )
    for item in summary["design_constraints_for_v2"]:
        rows.append(f"- {item}")
    rows.extend(
        [
            "",
            "## Interpretation",
            "",
            "The main failure is not lack of model capability: plain requery fixes more items than proposed PN/PE. The next method should add a selector and safer edge policy instead of adding more edge text.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R253 transfer failure mechanisms.")
    parser.add_argument("--results_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_failure_mechanism_analysis(
        results_jsonl=args.results_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
