from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_jsonl
from experiment.mmlu.r234_tiny_diagnostic_failure_analysis import load_audit_lookup
from experiment.mmlu.r237_apply_conservative_policy import build_source_lookup


VALID_LABELS = {"A", "B", "C", "D", "E"}


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label.startswith("NONE"):
        return "NONE"
    return label[:1] if label[:1] in VALID_LABELS else "NONE"


def _is_valid(value: Any) -> bool:
    return normalize_label(value) in VALID_LABELS


def build_feature_row(
    manifest_row: Dict[str, Any],
    source_row: Dict[str, Any],
) -> Dict[str, Any]:
    policy_input = manifest_row.get("model_visible_input", {})
    baseline = normalize_label(policy_input.get("baseline_prediction"))
    objective = normalize_label(policy_input.get("objective_prediction"))
    true_answer = normalize_label(source_row.get("true_answer") or source_row.get("gold_answer"))
    clean_label = source_row.get("clean_label", "unknown")
    baseline_correct = baseline == true_answer if true_answer in VALID_LABELS else None
    objective_correct = objective == true_answer if true_answer in VALID_LABELS else None
    harmful_switch = baseline_correct is True and objective_correct is False
    beneficial_switch = baseline_correct is False and objective_correct is True

    features = {
        "objective_differs": bool(policy_input.get("objective_prediction_differs_from_baseline")),
        "objective_top_score": int(policy_input.get("objective_top_score") or 0),
        "baseline_prediction_valid": _is_valid(baseline),
        "objective_prediction_valid": _is_valid(objective),
        "baseline_direct_majority_valid": _is_valid(policy_input.get("baseline_direct_majority")),
        "baseline_direct_majority_count": int(policy_input.get("baseline_direct_majority_count") or 0),
        "baseline_direct_valid_vote_count": int(policy_input.get("baseline_direct_valid_vote_count") or 0),
        "baseline_direct_votes_split": bool(policy_input.get("baseline_direct_votes_split")),
        "baseline_majority_equals_prediction": (
            normalize_label(policy_input.get("baseline_direct_majority")) == baseline
            if _is_valid(baseline)
            else False
        ),
    }
    labels = {
        "baseline_correct": baseline_correct,
        "objective_correct": objective_correct,
        "beneficial_switch": beneficial_switch,
        "harmful_switch": harmful_switch,
        "clean_harm_if_switch": harmful_switch and clean_label == "clean",
    }
    return {
        "task_id": manifest_row.get("task_id"),
        "split_role": manifest_row.get("split_role"),
        "training_allowed": bool(manifest_row.get("training_allowed")),
        "frozen_eval_only": bool(manifest_row.get("frozen_eval_only")),
        "baseline_prediction": baseline,
        "objective_prediction": objective,
        "true_answer": true_answer,
        "clean_label": clean_label,
        "features": features,
        "labels": labels,
        "model_visible_feature_keys": sorted(features.keys()),
        "label_keys_not_model_visible": sorted(labels.keys()) + ["true_answer", "clean_label"],
    }


def summarize_feature_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "rows": len(rows),
        "train_rows": sum(1 for row in rows if row.get("split_role") == "train"),
        "frozen_eval_rows": sum(1 for row in rows if row.get("split_role") == "frozen_eval"),
        "training_allowed_rows": sum(1 for row in rows if row.get("training_allowed")),
        "frozen_eval_only_rows": sum(1 for row in rows if row.get("frozen_eval_only")),
        "clean_labels": dict(sorted(Counter(row.get("clean_label", "unknown") for row in rows).items())),
        "beneficial_switch_labels": sum(1 for row in rows if row["labels"]["beneficial_switch"]),
        "harmful_switch_labels": sum(1 for row in rows if row["labels"]["harmful_switch"]),
        "clean_harm_if_switch_labels": sum(1 for row in rows if row["labels"]["clean_harm_if_switch"]),
    }


def run_feature_table_export(
    manifest_jsonl: str,
    source_paths: List[str],
    audit_paths: List[str],
    output_jsonl: str,
    summary_json: str,
    report_md: str,
) -> Dict[str, Any]:
    manifest_rows = load_jsonl(manifest_jsonl)
    source_lookup = build_source_lookup(source_paths)
    audit_lookup = load_audit_lookup(audit_paths)
    rows: List[Dict[str, Any]] = []
    missing_source: List[str] = []
    for row in manifest_rows:
        task_id = str(row.get("task_id") or "")
        source = dict(source_lookup.get(task_id) or {})
        if not source:
            missing_source.append(task_id)
            source = {"true_answer": "NONE"}
        source.update(audit_lookup.get(task_id, {}))
        rows.append(build_feature_row(row, source))

    summary = summarize_feature_rows(rows)
    summary.update(
        {
            "run_id": "R241",
            "title": "Abstention policy feature table",
            "claim_boundary": "Feature-table export only; no API, no trained-policy claim, and no SCI-Q2 readiness claim.",
            "no_api": True,
            "manifest_jsonl": manifest_jsonl,
            "source_paths": source_paths,
            "audit_paths": audit_paths,
            "output_jsonl": output_jsonl,
            "missing_source": missing_source,
            "feature_label_separation": "features are model-visible; labels/true_answer/clean_label are supervision/evaluation only",
        }
    )

    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for row in rows:
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
            "# R241 Abstention Policy Feature Table",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Rows: `{summary['rows']}`",
            f"- Train/frozen: `{summary['train_rows']}/{summary['frozen_eval_rows']}`",
            f"- Beneficial switch labels: `{summary['beneficial_switch_labels']}`",
            f"- Harmful switch labels: `{summary['harmful_switch_labels']}`",
            f"- Clean harm-if-switch labels: `{summary['clean_harm_if_switch_labels']}`",
            f"- Missing source: `{len(summary['missing_source'])}`",
            "",
            "## Boundary",
            "",
            "Feature columns are label-free and model-visible. Labels, true answers, and clean/noisy audit tags are only for training/evaluation.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export abstention policy feature table.")
    parser.add_argument("--manifest_jsonl", required=True)
    parser.add_argument("--source_paths", nargs="+", required=True)
    parser.add_argument("--audit_paths", nargs="*", default=[])
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_feature_table_export(
        manifest_jsonl=args.manifest_jsonl,
        source_paths=args.source_paths,
        audit_paths=args.audit_paths,
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
