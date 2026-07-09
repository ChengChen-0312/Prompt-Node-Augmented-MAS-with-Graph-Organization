from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple

import networkx as nx

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402
from experiment.aqua.graph_policy_pt_export import export_positive_policy_pt_dataset  # noqa: E402
from experiment.aqua.prompt_node_graph import attach_prompt_edge_metadata  # noqa: E402


RULE_NAME = "r163_r001_selective_promptedge_policy_export"

FORBIDDEN_SELECTOR_FIELDS = {
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


def _field_violates(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key in FORBIDDEN_SELECTOR_FIELDS or _field_violates(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_field_violates(child) for child in value)
    return False


def _policy_key(task_id: Any, slice_prefix: Any) -> tuple[str, str]:
    return str(task_id), str(slice_prefix)


def _graph_with_edge_metadata(target: Dict[str, Any]) -> Dict[str, Any]:
    roles = list(target.get("roles") or [])
    graph = nx.DiGraph()
    for index, role in enumerate(roles):
        graph.add_node(index, role=role)
    for edge in target.get("edges") or []:
        if isinstance(edge, (list, tuple)) and len(edge) == 2:
            graph.add_edge(int(edge[0]), int(edge[1]))
    annotated = attach_prompt_edge_metadata(graph)
    target = dict(target)
    target["prompt_edge_type_counts"] = dict(
        annotated.graph.get("prompt_edge_type_counts") or {}
    )
    target["prompt_node_edge_permissions"] = dict(
        target.get("prompt_node_edge_permissions") or {}
    )
    return target


def build_selective_promptedge_policy_rows(
    r077_rows: Sequence[Dict[str, Any]],
    r112_rows: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    r112_by_key = {
        _policy_key(row.get("task_id"), row.get("slice_prefix")): row
        for row in r112_rows
    }
    rows: List[Dict[str, Any]] = []
    action_counts: Counter[str] = Counter()
    edge_counts: Counter[str] = Counter()
    violations = 0
    matched_r112_rows = 0

    for source in r077_rows:
        selector_input = dict(source.get("selector_policy_input") or {})
        target_wrapper = dict(source.get("clean_fix_distillation_target") or {})
        target = dict(target_wrapper.get("graph_policy_target") or {})
        key = _policy_key(source.get("source_task_id"), source.get("source_slice_prefix"))
        objective_row = r112_by_key.get(key, {})
        if objective_row:
            matched_r112_rows += 1
        objective_input = dict(objective_row.get("policy_input") or {})
        target_action = str(objective_row.get("target_action") or "fallback_to_arg")
        objective_features = dict(
            selector_input.get("label_free_objective_features") or {}
        )
        graph_observation = dict(selector_input.get("candidate_graph_observation") or {})
        margin = float(
            objective_features.get("score_margin_to_next")
            or target.get("score_margin_to_next")
            or 0
        )
        has_promptnodes = bool(graph_observation.get("num_prompt_nodes"))
        should_insert = (
            target_action == "switch_to_objective"
            and target_wrapper.get("target_class") == "clean_fix_preserve_graph"
            and int(target.get("candidate_label", 0) or 0) == 1
            and has_promptnodes
            and margin >= 3
        )
        action = "insert_promptnode_graph" if should_insert else "fallback_to_arg_graph"
        action_counts[action] += 1
        target = _graph_with_edge_metadata(target) if should_insert else dict(target)
        if not should_insert:
            target["candidate_label"] = 0
        edge_counts.update(target.get("prompt_edge_type_counts") or {})
        row = {
            "rule": RULE_NAME,
            "source_slice_prefix": source.get("source_slice_prefix"),
            "source_candidate_method": source.get("source_candidate_method"),
            "selector_policy_input": {
                "slice_prefix": selector_input.get("slice_prefix"),
                "question": selector_input.get("question"),
                "candidate_method": selector_input.get("candidate_method"),
                "objective_bucket": objective_features.get("objective_bucket"),
                "score_margin_to_next": margin,
                "objective_prediction_differs_from_baseline": bool(
                    objective_input.get("objective_prediction_differs_from_baseline")
                ),
                "baseline_direct_votes_split": bool(
                    objective_input.get("baseline_direct_votes_split")
                ),
                "objective_top_score": objective_input.get("objective_top_score"),
                "candidate_graph_observation": graph_observation,
            },
            "selective_action": action,
            "graph_policy_target": target,
            "claim_boundary": (
                "R001-compatible selective PromptNode/PromptEdge policy target. "
                "Selector-visible fields exclude gold answers, predictions, "
                "correctness, audit labels, clean/noisy labels, and task ids."
            ),
        }
        if _field_violates(row["selector_policy_input"]):
            violations += 1
        rows.append(row)

    summary = {
        "rule": RULE_NAME,
        "source_r077_rows": len(r077_rows),
        "source_r112_rows": len(r112_rows),
        "matched_r112_rows": matched_r112_rows,
        "exported_rows": len(rows),
        "selective_insert_rows": action_counts.get("insert_promptnode_graph", 0),
        "fallback_rows": action_counts.get("fallback_to_arg_graph", 0),
        "prompt_edge_type_counts": dict(sorted(edge_counts.items())),
        "selector_input_forbidden_field_violations": violations,
        "forbidden_selector_fields": sorted(FORBIDDEN_SELECTOR_FIELDS),
        "claim_boundary": "Offline target export only; no API calls and no answer-accuracy claim.",
    }
    return rows, summary


def _to_pt_export_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    export_rows = []
    for index, row in enumerate(rows):
        if row.get("selective_action") != "insert_promptnode_graph":
            continue
        export_rows.append(
            {
                "task_id": f"r163_selective_{index:04d}",
                "slice_prefix": row.get("source_slice_prefix"),
                "candidate_method": row.get("source_candidate_method"),
                "policy_input": row.get("selector_policy_input") or {},
                "graph_policy_target": row.get("graph_policy_target") or {},
            }
        )
    return export_rows


def export_selective_positive_pt_dataset(
    rows: Sequence[Dict[str, Any]], output_dir: str
):
    return export_positive_policy_pt_dataset(_to_pt_export_rows(rows), output_dir)


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def render_report(
    summary: Dict[str, Any],
    pt_summary: Dict[str, Any],
    output_jsonl: str,
    manifest_jsonl: str,
) -> str:
    edge_counts = summary.get("prompt_edge_type_counts") or {}
    edge_text = ", ".join(f"{key}={value}" for key, value in edge_counts.items()) or "none"
    return "\n".join(
        [
            "# R163 R001-Style Selective PromptNode/PromptEdge Policy Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Inputs",
            "",
            "- Source rows: R077 clean-fix graph-policy distillation.",
            "- Objective-safety features: R112 first200 targets.",
            "- API calls: `0`.",
            "- Answer accuracy claim: `none`.",
            "",
            "## Export Summary",
            "",
            f"- Policy rows: `{summary['exported_rows']}`",
            f"- Selective insert rows: `{summary['selective_insert_rows']}`",
            f"- Fallback rows: `{summary['fallback_rows']}`",
            f"- Matched R112 rows: `{summary['matched_r112_rows']}`",
            f"- Selector forbidden-field violations: `{summary['selector_input_forbidden_field_violations']}`",
            f"- PromptEdge type counts: `{edge_text}`",
            f"- Output JSONL: `{output_jsonl}`",
            "",
            "## PyG Export",
            "",
            f"- Manifest JSONL: `{manifest_jsonl}`",
            f"- PT files: `{pt_summary['exported_pt_files']}`",
            f"- PromptNode PT files: `{pt_summary['promptnode_pt_files']}`",
            f"- PromptNode edge-permission PT files: `{pt_summary['promptnode_edge_permission_pt_files']}`",
            f"- PT outcome-field violations: `{pt_summary['outcome_field_violations']}`",
            "",
            "## Interpretation",
            "",
            "R163 moves the next branch back toward the R001 training paradigm: "
            "the exported positives are graph targets that contain PromptNodes and "
            "PromptEdge metadata before execution. Unlike R055, the export is "
            "selective: fallback rows are explicitly represented and only "
            "objective-safety switch rows with high-margin PromptNode graph targets "
            "become positive `.pt` files.",
            "",
            "This is not a result that PromptNodes improve AQuA accuracy. The next "
            "step is R164: train or smoke-test ARGDesigner's graph generator on "
            "these selective targets, then audit at R165 before broad API use.",
            "",
        ]
    )


def write_r163_artifacts(
    r077_jsonl: str,
    r112_jsonl: str,
    output_jsonl: str,
    pt_output_dir: str,
    manifest_jsonl: str,
    summary_json: str,
    report_md: str,
) -> Dict[str, Any]:
    r077_rows = load_jsonl_rows(r077_jsonl)
    r112_rows = load_jsonl_rows(r112_jsonl)
    rows, summary = build_selective_promptedge_policy_rows(r077_rows, r112_rows)
    manifest, pt_summary = export_selective_positive_pt_dataset(rows, pt_output_dir)
    summary = dict(summary)
    summary["pt_summary"] = pt_summary
    summary["output_jsonl"] = output_jsonl
    summary["manifest_jsonl"] = manifest_jsonl
    summary["report_md"] = report_md
    write_jsonl(output_jsonl, rows)
    write_jsonl(manifest_jsonl, manifest)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary, pt_summary, output_jsonl, manifest_jsonl))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export R001-compatible selective PromptNode/PromptEdge policy targets."
    )
    parser.add_argument(
        "--r077-jsonl",
        default="experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl",
    )
    parser.add_argument(
        "--r112-jsonl",
        default="experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl",
    )
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_first200_r163_selective_promptedge_policy_rows.jsonl",
    )
    parser.add_argument(
        "--pt-output-dir",
        default="experiment/FinetuneData_AQuA_R163_selective_promptedge",
    )
    parser.add_argument(
        "--manifest-jsonl",
        default="experiment/aqua/aqua_first200_r163_selective_promptedge_pt_manifest.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_r163_selective_promptedge_policy_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_r163_selective_promptedge_policy_report.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = write_r163_artifacts(
        r077_jsonl=args.r077_jsonl,
        r112_jsonl=args.r112_jsonl,
        output_jsonl=args.output_jsonl,
        pt_output_dir=args.pt_output_dir,
        manifest_jsonl=args.manifest_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
