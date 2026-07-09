from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from typing import Any, Dict, Iterable, List


ALLOWED_POLICY_INPUT_FIELDS = [
    "baseline_prediction",
    "objective_prediction",
    "objective_prediction_differs_from_baseline",
    "objective_top_score",
    "baseline_direct_majority",
    "baseline_direct_majority_count",
    "baseline_direct_valid_vote_count",
    "baseline_direct_votes_split",
]
FORBIDDEN_MODEL_VISIBLE_FIELDS = [
    "task_id",
    "analysis",
    "clean_label",
    "gold_binding_status",
    "rationale_issue",
    "true_answer",
    "is_correct",
    "correctness",
    "audit_label",
    "source_run",
]
OPTION_LABELS = ["A", "B", "C", "D", "E"]


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _normalize_option(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text if text in OPTION_LABELS else "NONE"


def build_router_target(row: Dict[str, Any], split_role: str) -> Dict[str, Any]:
    policy_input = row.get("policy_input", {})
    visible_input = {
        field: policy_input.get(field)
        for field in ALLOWED_POLICY_INPUT_FIELDS
        if field in policy_input
    }

    source_action = str(row.get("target_action", "fallback_to_arg"))
    objective_label = _normalize_option(policy_input.get("objective_prediction"))
    if source_action == "switch_to_objective" and objective_label != "NONE":
        router_action = "switch_to_objective"
        target_option_label = objective_label
    else:
        router_action = "abstain"
        target_option_label = "NONE"

    frozen_eval_only = split_role == "frozen_eval"
    training_allowed = split_role == "train"
    return {
        "task_id": row.get("task_id"),
        "source_run": row.get("source_run"),
        "split_role": split_role,
        "training_allowed": training_allowed,
        "frozen_eval_only": frozen_eval_only,
        "source_target_action": source_action,
        "router_action": router_action,
        "target_option_label": target_option_label,
        "target_reason": row.get("target_reason", ""),
        "model_visible_input": visible_input,
        "router_final_schema": {
            "schema_version": "r217_non_abstain_router_v1",
            "target_kind": "router_final_objective_safety",
            "allowed_option_labels": OPTION_LABELS + ["NONE"],
            "model_visible_fields": [f"policy_input.{field}" for field in visible_input],
            "forbidden_model_visible_fields": list(FORBIDDEN_MODEL_VISIBLE_FIELDS),
            "gold_answer_used": False,
            "tail34_training_allowed": False,
            "label_policy": (
                "switch_to_objective labels come from label-free objective-safety "
                "policy targets, not gold answer/correctness fields."
            ),
        },
    }


def scan_target_records(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(records)
    violations: List[Dict[str, Any]] = []
    action_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()

    for idx, row in enumerate(rows):
        action_counts[str(row.get("router_action", ""))] += 1
        split_counts[str(row.get("split_role", ""))] += 1
        visible_keys = set(row.get("model_visible_input", {}).keys())
        forbidden_overlap = sorted(visible_keys & set(FORBIDDEN_MODEL_VISIBLE_FIELDS))
        if forbidden_overlap:
            violations.append(
                {
                    "row_index": idx,
                    "reason": "forbidden_model_visible_fields",
                    "fields": forbidden_overlap,
                }
            )
        if row.get("split_role") == "frozen_eval" and row.get("training_allowed"):
            violations.append(
                {
                    "row_index": idx,
                    "reason": "frozen_eval_training_allowed",
                }
            )
        schema = row.get("router_final_schema", {})
        if schema.get("gold_answer_used") is not False:
            violations.append(
                {
                    "row_index": idx,
                    "reason": "gold_answer_used_not_false",
                }
            )

    return {
        "records": len(rows),
        "router_actions": dict(sorted(action_counts.items())),
        "split_roles": dict(sorted(split_counts.items())),
        "leakage_violations": len(violations),
        "leakage_pass": len(violations) == 0,
        "violations": violations,
    }


def export_router_targets(
    train_jsonl: str,
    frozen_eval_jsonl: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
) -> Dict[str, Any]:
    train_rows = load_jsonl(train_jsonl)
    frozen_rows = load_jsonl(frozen_eval_jsonl)
    targets = [build_router_target(row, "train") for row in train_rows]
    targets.extend(build_router_target(row, "frozen_eval") for row in frozen_rows)
    scan = scan_target_records(targets)

    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for row in targets:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "run_id": "R217",
        "title": "Non-abstain router-final target extraction",
        "claim_boundary": "Target extraction only; no API and no accuracy claim.",
        "no_api": True,
        "train_jsonl": train_jsonl,
        "frozen_eval_jsonl": frozen_eval_jsonl,
        "output_jsonl": output_jsonl,
        "train_source_rows": len(train_rows),
        "frozen_eval_source_rows": len(frozen_rows),
        **scan,
        "training_allowed_records": sum(1 for row in targets if row["training_allowed"]),
        "frozen_eval_only_records": sum(1 for row in targets if row["frozen_eval_only"]),
    }

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
            "# R217 Non-Abstain Router-Final Targets",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Train source rows: `{summary['train_source_rows']}`",
            f"- Frozen eval source rows: `{summary['frozen_eval_source_rows']}`",
            f"- Output records: `{summary['records']}`",
            f"- Router actions: `{summary['router_actions']}`",
            f"- Split roles: `{summary['split_roles']}`",
            f"- Leakage violations: `{summary['leakage_violations']}`",
            f"- Leakage pass: `{summary['leakage_pass']}`",
            "",
            "## Boundary",
            "",
            "These targets create non-abstain router labels from label-free objective-safety rows. They are not answer-accuracy results, and frozen tail34 rows must not be used for training.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export non-abstain router-final targets.")
    parser.add_argument("--train_jsonl", required=True)
    parser.add_argument("--frozen_eval_jsonl", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = export_router_targets(
        train_jsonl=args.train_jsonl,
        frozen_eval_jsonl=args.frozen_eval_jsonl,
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
