import argparse
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402


RULE_NAME = "r077_clean_fix_preserving_graph_policy_distill"

FORBIDDEN_SELECTOR_INPUT_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "task_id",
    "source_task_id",
}

GRAPH_TARGET_FIELDS = [
    "candidate_label",
    "training_target",
    "objective_reward",
    "score_components",
    "score_margin_to_next",
    "roles",
    "edges",
    "prompt_node_roles",
    "prompt_node_role_counts",
    "prompt_node_specs",
    "edge_role_pairs",
    "prompt_node_edge_role_pairs",
    "prompt_node_edge_permissions",
    "graph_signature",
]

AMBIGUOUS_TARGETS = {"multi_view_tie", "low_margin_top", "non_positive_top"}


def _field_violates(value: Any, forbidden_fields: set[str]) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden_fields:
                return True
            if _field_violates(child, forbidden_fields):
                return True
    elif isinstance(value, list):
        return any(_field_violates(child, forbidden_fields) for child in value)
    return False


def _sanitized_graph_target(target: Dict[str, Any]) -> Dict[str, Any]:
    clean_target = {field: target.get(field) for field in GRAPH_TARGET_FIELDS if field in target}
    clean_target["num_prompt_nodes"] = len(clean_target.get("prompt_node_roles") or [])
    clean_target["num_prompt_node_edges"] = len(clean_target.get("prompt_node_edge_role_pairs") or [])
    return clean_target


def _safe_score_components(target: Dict[str, Any]) -> Dict[str, Any]:
    score_components = target.get("score_components") or {}
    return {
        "strong_contract": int(score_components.get("strong_contract") or 0),
        "direct_agreement": int(score_components.get("direct_agreement") or 0),
        "direct_vote_support": int(score_components.get("direct_vote_support") or 0),
        "prompt_node_graph": int(score_components.get("prompt_node_graph") or 0),
        "conflict_penalty": int(score_components.get("conflict_penalty") or 0),
        "weak_contract_penalty": int(score_components.get("weak_contract_penalty") or 0),
    }


def _selector_input(row: Dict[str, Any], graph_target: Dict[str, Any]) -> Dict[str, Any]:
    policy_input = row.get("policy_input") or {}
    score_margin = graph_target.get("score_margin_to_next")
    objective_bucket = str(graph_target.get("training_target") or "unknown")
    return {
        "slice_prefix": policy_input.get("slice_prefix") or row.get("slice_prefix"),
        "question": policy_input.get("question"),
        "candidate_method": policy_input.get("candidate_method") or row.get("candidate_method"),
        "label_free_objective_features": {
            "objective_bucket": objective_bucket,
            "objective_bucket_flags": {
                "preferred_graph": objective_bucket == "preferred_graph",
                "multi_view_tie": objective_bucket == "multi_view_tie",
                "low_margin_top": objective_bucket == "low_margin_top",
                "non_positive_top": objective_bucket == "non_positive_top",
                "non_preferred_graph": objective_bucket == "non_preferred_graph",
            },
            "objective_reward": graph_target.get("objective_reward"),
            "score_margin_to_next": score_margin,
            "has_margin_at_least_3": isinstance(score_margin, (int, float)) and score_margin >= 3,
            "score_components": _safe_score_components(graph_target),
        },
        "candidate_graph_observation": {
            "num_prompt_nodes": graph_target["num_prompt_nodes"],
            "num_prompt_node_edges": graph_target["num_prompt_node_edges"],
            "prompt_node_role_counts": graph_target.get("prompt_node_role_counts") or {},
            "prompt_node_edge_role_pairs": graph_target.get("prompt_node_edge_role_pairs") or [],
            "has_promptnode_specs": bool(graph_target.get("prompt_node_specs")),
            "has_promptnode_edge_permissions": bool(graph_target.get("prompt_node_edge_permissions")),
        },
    }


def _is_clean_fix_preserve_target(graph_target: Dict[str, Any]) -> bool:
    score_margin = graph_target.get("score_margin_to_next")
    return (
        int(graph_target.get("candidate_label") or 0) == 1
        and graph_target.get("training_target") == "preferred_graph"
        and graph_target["num_prompt_nodes"] > 0
        and bool(graph_target.get("prompt_node_specs"))
        and bool(graph_target.get("prompt_node_edge_permissions"))
        and isinstance(score_margin, (int, float))
        and score_margin >= 3
    )


def _target_class(graph_target: Dict[str, Any]) -> Tuple[str, str, str]:
    training_target = str(graph_target.get("training_target"))
    if _is_clean_fix_preserve_target(graph_target):
        return (
            "clean_fix_preserve_graph",
            "preserve_high_margin_promptnode_graph",
            "high",
        )
    if training_target in AMBIGUOUS_TARGETS:
        return (
            "ambiguous_or_low_margin_suppress",
            "suppress_unstable_or_low_margin_switch",
            "suppress",
        )
    return ("negative_graph_suppress", "prefer_baseline_or_wait_for_more_evidence", "suppress")


def build_clean_fix_graph_policy_rows(
    policy_rows: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    target_counts: Counter[str] = Counter()
    teacher_counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()
    slice_counts: Counter[str] = Counter()
    clean_fix_promptnode_spec_rows = 0
    clean_fix_edge_permission_rows = 0

    for row in policy_rows:
        graph_target = _sanitized_graph_target(row.get("graph_policy_target") or {})
        target_class, teacher_policy, preserve_priority = _target_class(graph_target)
        selector_input = _selector_input(row, graph_target)
        clean_fix_target = {
            "target_class": target_class,
            "teacher_policy": teacher_policy,
            "preserve_priority": preserve_priority,
            "candidate_label": graph_target.get("candidate_label"),
            "graph_policy_target": graph_target,
            "claim_boundary": (
                "Clean-fix-preserving distillation target. Tail34 clean/noisy evidence defines the schema only; "
                "selector inputs contain label-free graph/objective features and no answers, audit labels, "
                "correctness fields, or task ids."
            ),
        }
        output_row = {
            "source_task_id": row.get("task_id"),
            "source_slice_prefix": row.get("slice_prefix"),
            "source_candidate_method": row.get("candidate_method"),
            "selector_policy_input": selector_input,
            "clean_fix_distillation_target": clean_fix_target,
        }
        rows.append(output_row)
        target_counts[target_class] += 1
        teacher_counts[teacher_policy] += 1
        method_counts[str(row.get("candidate_method"))] += 1
        slice_counts[str(row.get("slice_prefix"))] += 1
        if target_class == "clean_fix_preserve_graph":
            if graph_target.get("prompt_node_specs"):
                clean_fix_promptnode_spec_rows += 1
            if graph_target.get("prompt_node_edge_permissions"):
                clean_fix_edge_permission_rows += 1

    selector_input_violations = sum(
        1 for row in rows if _field_violates(row["selector_policy_input"], FORBIDDEN_SELECTOR_INPUT_FIELDS)
    )
    distillation_target_violations = sum(
        1
        for row in rows
        if _field_violates(
            row["clean_fix_distillation_target"]["graph_policy_target"],
            FORBIDDEN_SELECTOR_INPUT_FIELDS,
        )
    )
    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "source_policy_rows": len(policy_rows),
        "rows": len(rows),
        "clean_fix_preserve_rows": target_counts["clean_fix_preserve_graph"],
        "ambiguous_suppress_rows": target_counts["ambiguous_or_low_margin_suppress"],
        "negative_suppress_rows": target_counts["negative_graph_suppress"],
        "clean_fix_promptnode_spec_rows": clean_fix_promptnode_spec_rows,
        "clean_fix_edge_permission_rows": clean_fix_edge_permission_rows,
        "target_class_counts": dict(sorted(target_counts.items())),
        "teacher_policy_counts": dict(sorted(teacher_counts.items())),
        "candidate_method_counts": dict(sorted(method_counts.items())),
        "slice_counts": dict(sorted(slice_counts.items())),
        "selector_input_violations": selector_input_violations,
        "distillation_target_violations": distillation_target_violations,
        "excluded_selector_input_fields": sorted(FORBIDDEN_SELECTOR_INPUT_FIELDS),
        "tail34_evidence_used_as_schema_only": True,
        "tail34_schema_anchor": {
            "clean_positive_task_count": 3,
            "noisy_optional_task_count": 1,
            "unstable_boundary_task_count": 1,
            "schema_rule": "preserve clean-fix PromptNode channels; do not train noisy-only switches as clean positives",
        },
        "claim_boundary": (
            "R077 is a distillation-data artifact, not an answer-accuracy result. It uses R076 as schema guidance "
            "and first200 label-free graph-policy rows as trainable examples."
        ),
    }
    return rows, summary


def build_first200_clean_fix_graph_policy_rows(
    input_jsonl: str = "experiment/aqua/aqua_first200_graph_policy_distill_rows.jsonl",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    policy_rows = load_jsonl_rows(input_jsonl)
    rows, summary = build_clean_fix_graph_policy_rows(policy_rows)
    summary["input_jsonl"] = input_jsonl
    return rows, summary


def write_json(path: str, payload: Dict[str, Any]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _format_counts(counts: Dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def render_report(summary: Dict[str, Any], output_jsonl: str) -> str:
    return "\n".join(
        [
            "# R077 Clean-Fix-Preserving Graph-Policy Distillation",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Input rows: `{summary.get('input_jsonl')}`",
            f"- Output rows: `{output_jsonl}`",
            f"- Source policy rows: `{summary['source_policy_rows']}`",
            f"- Distillation rows: `{summary['rows']}`",
            f"- Clean-fix-preserve graph rows: `{summary['clean_fix_preserve_rows']}`",
            f"- Ambiguous/low-margin suppress rows: `{summary['ambiguous_suppress_rows']}`",
            f"- Negative suppress rows: `{summary['negative_suppress_rows']}`",
            f"- Clean-fix PromptNode spec rows: `{summary['clean_fix_promptnode_spec_rows']}`",
            f"- Clean-fix edge-permission rows: `{summary['clean_fix_edge_permission_rows']}`",
            f"- Selector-input violations: `{summary['selector_input_violations']}`",
            f"- Target-field violations: `{summary['distillation_target_violations']}`",
            f"- Target class counts: `{_format_counts(summary.get('target_class_counts', {}))}`",
            f"- Teacher policy counts: `{_format_counts(summary.get('teacher_policy_counts', {}))}`",
            "",
            "## Interpretation",
            "",
            "R077 converts the R076 clean-fix-preserving boundary into trainable graph-policy rows without using tail34 "
            "task labels as training examples. Tail34 evidence is used only to define the schema: preserve high-margin "
            "PromptNode graph channels, suppress ambiguous/low-margin switches, and do not treat noisy-only gains as "
            "clean positives.",
            "",
            "The positive rows still carry update2 PromptNode identities, permissions, budgets, lifecycle actions, and "
            "edge permissions through the nested graph-policy target. The selector input is deliberately narrower: task "
            "text, candidate method, label-free objective components, and graph observations only.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export clean-fix-preserving selector/graph-policy distillation rows from first200 policy rows."
    )
    parser.add_argument(
        "--input-jsonl",
        default="experiment/aqua/aqua_first200_graph_policy_distill_rows.jsonl",
    )
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_r077_clean_fix_graph_policy_distill_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_r077_clean_fix_graph_policy_distill_report.md",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows, summary = build_first200_clean_fix_graph_policy_rows(args.input_jsonl)
    write_jsonl(args.output_jsonl, rows)
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary, args.output_jsonl))
    print(
        "Exported clean-fix graph-policy distillation rows: "
        f"rows={summary['rows']} clean_fix={summary['clean_fix_preserve_rows']} "
        f"selector_violations={summary['selector_input_violations']} "
        f"target_violations={summary['distillation_target_violations']}"
    )


if __name__ == "__main__":
    main()
