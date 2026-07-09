from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402
from experiment.aqua.graph_policy_pt_export import export_positive_policy_pt_dataset  # noqa: E402
from experiment.aqua.r001_selective_promptedge_policy_export import (  # noqa: E402
    FORBIDDEN_SELECTOR_FIELDS,
    _field_violates,
    _graph_with_edge_metadata,
    _policy_key,
    write_json,
    write_jsonl,
    write_text,
)


RULE_NAME = "r166_expanded_selective_promptedge_targets"


def _safe_margin(*values: Any) -> float:
    for value in values:
        if isinstance(value, (int, float)):
            return float(value)
        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            pass
    return 0.0


def _is_positive_preserve_target(
    target_wrapper: Dict[str, Any],
    target: Dict[str, Any],
    graph_observation: Dict[str, Any],
    margin: float,
) -> bool:
    return (
        target_wrapper.get("target_class") == "clean_fix_preserve_graph"
        and int(target.get("candidate_label", 0) or 0) == 1
        and bool(graph_observation.get("num_prompt_nodes"))
        and bool(graph_observation.get("has_promptnode_edge_permissions"))
        and margin >= 3
    )


def build_expanded_selective_promptedge_targets(
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
        objective_features = dict(
            selector_input.get("label_free_objective_features") or {}
        )
        graph_observation = dict(selector_input.get("candidate_graph_observation") or {})
        target_wrapper = dict(source.get("clean_fix_distillation_target") or {})
        target = dict(target_wrapper.get("graph_policy_target") or {})
        objective_row = r112_by_key.get(
            _policy_key(source.get("source_task_id"), source.get("source_slice_prefix")),
            {},
        )
        if objective_row:
            matched_r112_rows += 1
        objective_input = dict(objective_row.get("policy_input") or {})
        target_action = str(objective_row.get("target_action") or "fallback_to_arg")
        margin = _safe_margin(
            objective_features.get("score_margin_to_next"),
            target.get("score_margin_to_next"),
        )
        positive = _is_positive_preserve_target(
            target_wrapper, target, graph_observation, margin
        )
        if positive and target_action == "switch_to_objective":
            selective_action = "switch_critical_insert"
        elif positive:
            selective_action = "preserve_safe_insert"
        else:
            selective_action = "suppress_or_fallback"

        if positive:
            target = _graph_with_edge_metadata(target)
        else:
            target = dict(target)
            target["candidate_label"] = 0

        edge_counts.update(target.get("prompt_edge_type_counts") or {})
        action_counts[selective_action] += 1
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
                "has_margin_at_least_3": bool(
                    objective_features.get("has_margin_at_least_3")
                ),
                "objective_prediction_differs_from_baseline": bool(
                    objective_input.get("objective_prediction_differs_from_baseline")
                ),
                "baseline_direct_votes_split": bool(
                    objective_input.get("baseline_direct_votes_split")
                ),
                "objective_top_score": objective_input.get("objective_top_score"),
                "candidate_graph_observation": graph_observation,
            },
            "selective_action": selective_action,
            "positive_graph_target": positive,
            "graph_policy_target": target,
            "claim_boundary": (
                "R166 expanded selective PromptNode/PromptEdge target. "
                "Switch-critical and preserve-safe positives are separated; "
                "selector-visible fields exclude gold answers, predictions, "
                "correctness, audit labels, clean/noisy labels, and task ids."
            ),
        }
        if _field_violates(row["selector_policy_input"]):
            violations += 1
        rows.append(row)

    positive_rows = (
        action_counts.get("switch_critical_insert", 0)
        + action_counts.get("preserve_safe_insert", 0)
    )
    summary = {
        "rule": RULE_NAME,
        "source_r077_rows": len(r077_rows),
        "source_r112_rows": len(r112_rows),
        "matched_r112_rows": matched_r112_rows,
        "exported_rows": len(rows),
        "positive_graph_rows": positive_rows,
        "switch_critical_insert_rows": action_counts.get("switch_critical_insert", 0),
        "preserve_safe_insert_rows": action_counts.get("preserve_safe_insert", 0),
        "suppress_or_fallback_rows": action_counts.get("suppress_or_fallback", 0),
        "prompt_edge_type_counts": dict(sorted(edge_counts.items())),
        "selector_input_forbidden_field_violations": violations,
        "forbidden_selector_fields": sorted(FORBIDDEN_SELECTOR_FIELDS),
        "claim_boundary": (
            "Offline expanded target export only; no API calls and no answer-accuracy claim."
        ),
    }
    return rows, summary


def _to_pt_export_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    export_rows = []
    for index, row in enumerate(rows):
        if not row.get("positive_graph_target"):
            continue
        export_rows.append(
            {
                "task_id": f"r166_expanded_{index:04d}",
                "slice_prefix": row.get("source_slice_prefix"),
                "candidate_method": row.get("source_candidate_method"),
                "policy_input": row.get("selector_policy_input") or {},
                "graph_policy_target": row.get("graph_policy_target") or {},
            }
        )
    return export_rows


def export_expanded_positive_pt_dataset(
    rows: Sequence[Dict[str, Any]], output_dir: str
):
    return export_positive_policy_pt_dataset(_to_pt_export_rows(rows), output_dir)


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
            "# R166 Expanded Selective PromptNode/PromptEdge Targets",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Export Summary",
            "",
            f"- Policy rows: `{summary['exported_rows']}`",
            f"- Positive graph rows: `{summary['positive_graph_rows']}`",
            f"- Switch-critical inserts: `{summary['switch_critical_insert_rows']}`",
            f"- Preserve-safe inserts: `{summary['preserve_safe_insert_rows']}`",
            f"- Suppress/fallback rows: `{summary['suppress_or_fallback_rows']}`",
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
            "R166 expands R163's sparse switch-only target set. The export keeps "
            "the four switch-critical PromptNode graphs, adds seventy-two "
            "preserve-safe PromptNode graphs for structure learning, and keeps "
            "seven hundred twenty-four rows as suppress/fallback selector "
            "negatives. This is still an offline target artifact, not an "
            "answer-accuracy result.",
            "",
        ]
    )


def write_r166_artifacts(
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
    rows, summary = build_expanded_selective_promptedge_targets(r077_rows, r112_rows)
    manifest, pt_summary = export_expanded_positive_pt_dataset(rows, pt_output_dir)
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
        description="Export expanded R166 selective PromptNode/PromptEdge targets."
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
        default="experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl",
    )
    parser.add_argument(
        "--pt-output-dir",
        default="experiment/FinetuneData_AQuA_R166_expanded_selective_promptedge",
    )
    parser.add_argument(
        "--manifest-jsonl",
        default="experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_pt_manifest.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_r166_expanded_selective_promptedge_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_r166_expanded_selective_promptedge_report.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = write_r166_artifacts(
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
