from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Sequence


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402


RULE_NAME = "r176_switch_critical_target_mining"
DEFAULT_R112_JSONL = "experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl"
DEFAULT_R077_JSONL = "experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl"
DEFAULT_R166_JSONL = "experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_first200_r176_switch_critical_target_mining_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_first200_r176_switch_critical_target_mining_report.md"
)


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _policy_key(task_id: Any, slice_prefix: Any) -> tuple[str, str]:
    return str(task_id), str(slice_prefix)


def _candidate_feature(row: Dict[str, Any]) -> Dict[str, Any]:
    selector_input = row.get("selector_policy_input") or {}
    objective = selector_input.get("label_free_objective_features") or {}
    observation = selector_input.get("candidate_graph_observation") or {}
    wrapper = row.get("clean_fix_distillation_target") or {}
    target = wrapper.get("graph_policy_target") or {}
    margin = _float(objective.get("score_margin_to_next") or target.get("score_margin_to_next"))
    candidate_label = int(target.get("candidate_label") or 0)
    num_prompt_nodes = int(observation.get("num_prompt_nodes") or 0)
    has_edge_permissions = bool(observation.get("has_promptnode_edge_permissions"))
    is_r166_switch_critical = bool(
        wrapper.get("target_class") == "clean_fix_preserve_graph"
        and candidate_label == 1
        and num_prompt_nodes > 0
        and has_edge_permissions
        and margin >= 3
    )
    return {
        "candidate_method": row.get("source_candidate_method"),
        "target_class": wrapper.get("target_class"),
        "candidate_label": candidate_label,
        "objective_bucket": objective.get("objective_bucket"),
        "objective_reward": _float(objective.get("objective_reward")),
        "score_margin_to_next": margin,
        "num_prompt_nodes": num_prompt_nodes,
        "has_promptnode_edge_permissions": has_edge_permissions,
        "graph_signature": target.get("graph_signature"),
        "is_r166_switch_critical": is_r166_switch_critical,
    }


def classify_switch_gap(
    r112_row: Dict[str, Any],
    candidate_features: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    if r112_row.get("target_action") != "switch_to_objective":
        return {
            "gap_class": "not_objective_switch",
            "claimable_override_label": False,
            "weak_expansion_candidate": False,
        }
    if any(feature.get("is_r166_switch_critical") for feature in candidate_features):
        return {
            "gap_class": "confirmed_switch_critical",
            "claimable_override_label": True,
            "weak_expansion_candidate": False,
        }
    promptnode_candidates = [
        feature for feature in candidate_features if int(feature.get("num_prompt_nodes") or 0) > 0
    ]
    if not promptnode_candidates:
        return {
            "gap_class": "no_promptnode_candidate",
            "claimable_override_label": False,
            "weak_expansion_candidate": False,
        }
    weak_candidates = [
        feature
        for feature in promptnode_candidates
        if feature.get("objective_bucket") == "multi_view_tie"
        and _float(feature.get("objective_reward")) >= 10
        and _float(feature.get("score_margin_to_next")) >= 3
        and bool(feature.get("has_promptnode_edge_permissions"))
    ]
    if weak_candidates:
        return {
            "gap_class": "weak_high_margin_tie_candidate",
            "claimable_override_label": False,
            "weak_expansion_candidate": True,
        }
    return {
        "gap_class": "low_confidence_promptnode_candidate",
        "claimable_override_label": False,
        "weak_expansion_candidate": False,
    }


def build_mining_summary(
    r112_jsonl: str = DEFAULT_R112_JSONL,
    r077_jsonl: str = DEFAULT_R077_JSONL,
    r166_jsonl: str = DEFAULT_R166_JSONL,
) -> Dict[str, Any]:
    r112_rows = load_jsonl_rows(r112_jsonl)
    r077_rows = load_jsonl_rows(r077_jsonl)
    r166_rows = load_jsonl_rows(r166_jsonl)
    r077_by_key: Dict[tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in r077_rows:
        r077_by_key[_policy_key(row.get("source_task_id"), row.get("source_slice_prefix"))].append(row)

    switch_rows = [row for row in r112_rows if row.get("target_action") == "switch_to_objective"]
    records: List[Dict[str, Any]] = []
    for row in switch_rows:
        key = _policy_key(row.get("task_id"), row.get("slice_prefix"))
        candidate_features = [_candidate_feature(candidate) for candidate in r077_by_key.get(key, [])]
        classification = classify_switch_gap(row, candidate_features)
        records.append(
            {
                "task_id": row.get("task_id"),
                "slice_prefix": row.get("slice_prefix"),
                "policy_input": row.get("policy_input") or {},
                "target_action": row.get("target_action"),
                "candidate_count": len(candidate_features),
                "candidate_features": candidate_features,
                **classification,
            }
        )

    gap_counts = Counter(record["gap_class"] for record in records)
    weak_records = [record for record in records if record.get("weak_expansion_candidate")]
    confirmed_records = [record for record in records if record.get("claimable_override_label")]
    expanded_pool_records = confirmed_records + weak_records
    expanded_by_slice = Counter(record.get("slice_prefix") for record in expanded_pool_records)
    r166_switch_rows = sum(
        1 for row in r166_rows if row.get("selective_action") == "switch_critical_insert"
    )
    expanded_pool_size = len(expanded_pool_records)
    eval_expanded = expanded_by_slice.get("aqua_next100", 0)
    return {
        "rule": RULE_NAME,
        "r112_rows": len(r112_rows),
        "r077_rows": len(r077_rows),
        "r166_rows": len(r166_rows),
        "r112_switch_rows": len(switch_rows),
        "r166_switch_rows": r166_switch_rows,
        "gap_class_counts": dict(sorted(gap_counts.items())),
        "confirmed_switch_critical_rows": len(confirmed_records),
        "weak_high_margin_tie_rows": len(weak_records),
        "expanded_override_pool_if_weak_included": expanded_pool_size,
        "expanded_override_pool_by_slice": dict(sorted(expanded_by_slice.items())),
        "expanded_override_pool_still_insufficient": bool(
            expanded_pool_size < 20 or eval_expanded < 5
        ),
        "records": records,
        "claim_boundary": (
            "R176 is a no-API target-mining audit. Weak high-margin tie rows are "
            "diagnostic expansion candidates only; they are not claimable learned "
            "override labels without additional validation."
        ),
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{slice}` | `{cls}` | `{claim}` | `{weak}` | `{n}` |".format(
            task=record.get("task_id"),
            slice=record.get("slice_prefix"),
            cls=record.get("gap_class"),
            claim=record.get("claimable_override_label"),
            weak=record.get("weak_expansion_candidate"),
            n=record.get("candidate_count"),
        )
        for record in summary["records"]
    ]
    return "\n".join(
        [
            "# R176 Switch-Critical Target Mining Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- R112 switch rows: `{summary['r112_switch_rows']}`",
            f"- R166 switch rows: `{summary['r166_switch_rows']}`",
            f"- Gap class counts: `{summary['gap_class_counts']}`",
            f"- Confirmed switch-critical rows: `{summary['confirmed_switch_critical_rows']}`",
            f"- Weak high-margin tie rows: `{summary['weak_high_margin_tie_rows']}`",
            f"- Expanded pool if weak included: `{summary['expanded_override_pool_if_weak_included']}`",
            f"- Expanded pool by slice: `{summary['expanded_override_pool_by_slice']}`",
            f"- Expanded pool still insufficient: `{summary['expanded_override_pool_still_insufficient']}`",
            "",
            "| Task | Slice | Gap class | Claimable override | Weak expansion | Candidate rows |",
            "| --- | --- | --- | --- | --- | ---: |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R112 contains more potential switch decisions than R166, but the existing non-leaky "
            "graph-policy traces only provide four confirmed switch-critical PromptNode/PromptEdge "
            "targets. Two additional rows are high-margin multi-view ties and may be useful as weak "
            "curriculum examples, but treating them as confirmed override labels would overstate the "
            "evidence. Even with weak rows included, the override pool remains too small for a learned "
            "override-head claim.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mine switch-critical target gaps.")
    parser.add_argument("--r112-jsonl", default=DEFAULT_R112_JSONL)
    parser.add_argument("--r077-jsonl", default=DEFAULT_R077_JSONL)
    parser.add_argument("--r166-jsonl", default=DEFAULT_R166_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_mining_summary(
        _repo_path(args.r112_jsonl),
        _repo_path(args.r077_jsonl),
        _repo_path(args.r166_jsonl),
    )
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R176 switch-critical target mining audit: "
        f"confirmed={summary['confirmed_switch_critical_rows']} "
        f"weak={summary['weak_high_margin_tie_rows']} "
        f"insufficient={summary['expanded_override_pool_still_insufficient']}"
    )


if __name__ == "__main__":
    main()
