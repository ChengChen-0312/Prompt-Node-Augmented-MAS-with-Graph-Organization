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
from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_json


VARIANT_ORDER = [
    "arg_baseline_fixed",
    "abstain_keep_arg",
    "plain_requery",
    "node_only_no_promptedge_text",
    "proposed_promptnode_promptedge",
]


def _stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    evaluated = [row for row in rows if row.get("is_correct") is not None]
    correct = sum(1 for row in evaluated if row.get("is_correct"))
    return {
        "records": len(rows),
        "evaluated_records": len(evaluated),
        "correct": correct,
        "accuracy": correct / len(evaluated) if evaluated else None,
        "fixes": sum(1 for row in evaluated if row.get("fix")),
        "harms": sum(1 for row in evaluated if row.get("harm")),
    }


def summarize_by_variant_and_role(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_variant = {
        variant: _stats([row for row in rows if row.get("control_variant") == variant])
        for variant in sorted({str(row.get("control_variant")) for row in rows})
    }
    by_variant_role: Dict[str, Dict[str, Any]] = {}
    for variant in by_variant:
        by_variant_role[variant] = {}
        for role in sorted({str(row.get("selection_role")) for row in rows}):
            by_variant_role[variant][role] = _stats(
                [
                    row
                    for row in rows
                    if row.get("control_variant") == variant and row.get("selection_role") == role
                ]
            )
    return {
        "rows": len(rows),
        "by_variant": by_variant,
        "by_variant_role": by_variant_role,
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in rows).items())),
    }


def _correct(summary: Dict[str, Any], variant: str) -> int:
    return int(summary["by_variant"].get(variant, {}).get("correct") or 0)


def _harms(summary: Dict[str, Any], variant: str) -> int:
    return int(summary["by_variant"].get(variant, {}).get("harms") or 0)


def assess_transfer_claims(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = summarize_by_variant_and_role(rows)
    proposed = _correct(summary, "proposed_promptnode_promptedge")
    baseline = _correct(summary, "arg_baseline_fixed")
    plain = _correct(summary, "plain_requery")
    node_only = _correct(summary, "node_only_no_promptedge_text")
    proposed_harms = _harms(summary, "proposed_promptnode_promptedge")
    node_harms = _harms(summary, "node_only_no_promptedge_text")
    return {
        "proposed_correct": proposed,
        "arg_baseline_correct": baseline,
        "plain_requery_correct": plain,
        "node_only_correct": node_only,
        "proposed_net_correct_vs_arg": proposed - baseline,
        "proposed_beats_arg_baseline": proposed > baseline,
        "proposed_beats_plain_requery": proposed > plain,
        "proposed_beats_node_only": proposed > node_only,
        "promptedge_text_gain_supported": proposed > node_only and proposed_harms <= node_harms,
        "transfer_superiority_supported": proposed > baseline
        and proposed > plain
        and proposed > node_only
        and proposed_harms == 0,
        "recommended_claim": (
            "negative_transfer_diagnostic"
            if not (proposed > plain and proposed > node_only)
            else "requires_more_evidence"
        ),
    }


def _changed_cases(rows: List[Dict[str, Any]], variant: str) -> List[Dict[str, Any]]:
    selected = []
    for row in rows:
        if row.get("control_variant") != variant:
            continue
        if row.get("fix") or row.get("harm"):
            selected.append(
                {
                    "task_id": row.get("task_id"),
                    "selection_role": row.get("selection_role"),
                    "arg_prediction": row.get("arg_prediction"),
                    "predicted_answer": row.get("predicted_answer"),
                    "true_answer": row.get("true_answer"),
                    "fix": bool(row.get("fix")),
                    "harm": bool(row.get("harm")),
                }
            )
    return selected


def run_result_analysis(
    results_jsonl: str,
    api_summary_json: str,
    summary_json: str,
    report_md: str,
) -> Dict[str, Any]:
    rows = load_jsonl(results_jsonl)
    api_summary = load_json(api_summary_json)
    summary = summarize_by_variant_and_role(rows)
    assessment = assess_transfer_claims(rows)
    output = {
        "run_id": "R254",
        "title": "MMLU tiny transfer result analysis",
        "claim_boundary": "Result analysis only; R253 is a tiny diagnostic and does not support SCI-Q2 readiness or transfer superiority.",
        "no_api": True,
        "broad_api": False,
        "results_jsonl": results_jsonl,
        "api_summary_json": api_summary_json,
        "api_cost": api_summary.get("api_cost"),
        "prompt_tokens": api_summary.get("prompt_tokens"),
        "completion_tokens": api_summary.get("completion_tokens"),
        **summary,
        "assessment": assessment,
        "proposed_changed_cases": _changed_cases(rows, "proposed_promptnode_promptedge"),
        "plain_changed_cases": _changed_cases(rows, "plain_requery"),
        "node_only_changed_cases": _changed_cases(rows, "node_only_no_promptedge_text"),
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
        "# R254 MMLU Tiny Transfer Result Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Variant Results",
        "",
        "| Variant | Correct | Accuracy | Fix/Harm |",
        "|---|---:|---:|---:|",
    ]
    for variant in VARIANT_ORDER:
        item = summary["by_variant"].get(variant, {"correct": 0, "accuracy": None, "fixes": 0, "harms": 0})
        rows.append(
            f"| `{variant}` | `{item['correct']}`/`{item['records']}` | `{item['accuracy']}` | `{item['fixes']}/{item['harms']}` |"
        )
    assessment = summary["assessment"]
    rows.extend(
        [
            "",
            "## Claim Assessment",
            "",
            f"- Proposed beats ARG baseline: `{assessment['proposed_beats_arg_baseline']}` (`{assessment['proposed_net_correct_vs_arg']}` net correct)",
            f"- Proposed beats plain requery: `{assessment['proposed_beats_plain_requery']}`",
            f"- Proposed beats node-only: `{assessment['proposed_beats_node_only']}`",
            f"- PromptEdge text gain supported: `{assessment['promptedge_text_gain_supported']}`",
            f"- Transfer superiority supported: `{assessment['transfer_superiority_supported']}`",
            "",
            "## Interpretation",
            "",
            "The tiny transfer diagnostic is negative for the current PN/PE prompt design: proposed PN/PE improves over fixed ARG but loses to plain requery and node-only. This supports a redesign/selector lesson, not a transfer superiority claim.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R253 MMLU tiny transfer results.")
    parser.add_argument("--results_jsonl", required=True)
    parser.add_argument("--api_summary_json", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_result_analysis(
        results_jsonl=args.results_jsonl,
        api_summary_json=args.api_summary_json,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
