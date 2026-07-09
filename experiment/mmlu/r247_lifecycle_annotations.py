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
from experiment.mmlu.r244_case_study_extraction import enrich_rows


def annotate_decision_lifecycle(row: Dict[str, Any]) -> Dict[str, Any]:
    actions: List[str] = []
    edge_actions: List[str] = ["read"]
    rationale: List[str] = []

    if row.get("switch") and row.get("fix"):
        actions.append("update")
        edge_actions.append("forward")
        rationale.append("Policy updates final state with objective/PromptNode evidence because it fixes ARG.")
        if row.get("split_role") == "frozen_eval" and row.get("clean_label") == "clean":
            actions.append("upgrade")
            rationale.append("Clean frozen fix is eligible for upgrading the pattern into a reusable policy case.")
    if (not row.get("switch")) and row.get("baseline_correct") is True and row.get("selected_correct") is True:
        actions.append("prune")
        rationale.append("Policy prunes objective/PromptNode evidence to protect an ARG-correct clean state.")
    if row.get("switch") and row.get("baseline_correct") is False and row.get("selected_correct") is False:
        actions.append("merge")
        rationale.append("Neither ARG nor objective evidence is sufficient; future policy needs merged multi-view evidence.")
    if row.get("harm"):
        actions.append("prune")
        rationale.append("Observed harm means this switch pattern should be pruned.")

    return {
        "annotation_type": "task_decision",
        "task_id": row.get("task_id"),
        "split_role": row.get("split_role"),
        "clean_label": row.get("clean_label", "unknown"),
        "lifecycle_actions": sorted(set(actions)),
        "edge_actions": sorted(set(edge_actions)),
        "baseline_prediction": row.get("baseline_prediction"),
        "objective_prediction": row.get("objective_prediction"),
        "selected_prediction": row.get("selected_prediction"),
        "true_answer": row.get("true_answer"),
        "rationale": rationale,
    }


def annotate_source_lifecycle(row: Dict[str, Any]) -> Dict[str, Any]:
    actions: List[str] = []
    edge_actions: List[str] = []
    rationale: List[str] = []
    promptnode_rate = float(row.get("promptnode_record_rate") or 0.0)
    positive = bool(row.get("positive_accuracy_source"))

    if promptnode_rate >= 0.9 and not positive:
        actions.append("compress")
        edge_actions.append("write")
        rationale.append("Dense PromptNode metadata exists but accuracy source is negative; compress before reuse.")
    if positive and promptnode_rate == 0.0:
        actions.append("upgrade")
        rationale.append("Positive source lacks first-class PromptNode roles; upgrade graph metadata before claiming PN mechanism.")
    if promptnode_rate > 0 and positive:
        actions.append("merge")
        rationale.append("Positive source with PromptNode metadata can seed merge of accuracy and mechanism evidence.")

    return {
        "annotation_type": "source_metadata",
        "run_id": row.get("run_id"),
        "source_path": row.get("path"),
        "positive_accuracy_source": positive,
        "promptnode_record_rate": promptnode_rate,
        "lifecycle_actions": sorted(set(actions)),
        "edge_actions": sorted(set(edge_actions)),
        "rationale": rationale,
    }


def summarize_lifecycle_annotations(annotations: List[Dict[str, Any]]) -> Dict[str, Any]:
    lifecycle_counts = Counter()
    edge_counts = Counter()
    type_counts = Counter()
    for row in annotations:
        type_counts[row.get("annotation_type", "unknown")] += 1
        lifecycle_counts.update(row.get("lifecycle_actions", []))
        edge_counts.update(row.get("edge_actions", []))
    return {
        "annotations": len(annotations),
        "annotation_type_counts": dict(sorted(type_counts.items())),
        "lifecycle_action_counts": dict(sorted(lifecycle_counts.items())),
        "edge_action_counts": dict(sorted(edge_counts.items())),
    }


def run_lifecycle_annotation(
    decision_records_jsonl: str,
    source_metadata_jsonl: str,
    source_paths: List[str],
    audit_paths: List[str],
    output_jsonl: str,
    summary_json: str,
    report_md: str,
) -> Dict[str, Any]:
    decision_rows = enrich_rows(load_jsonl(decision_records_jsonl), source_paths, audit_paths)
    annotations = [annotate_decision_lifecycle(row) for row in decision_rows]
    annotations.extend(annotate_source_lifecycle(row) for row in load_jsonl(source_metadata_jsonl))
    summary = summarize_lifecycle_annotations(annotations)
    summary.update(
        {
            "run_id": "R247",
            "title": "PromptNode lifecycle annotations",
            "claim_boundary": "Lifecycle annotation only; no API, no accuracy claim, and no SCI-Q2 readiness claim.",
            "no_api": True,
            "decision_records_jsonl": decision_records_jsonl,
            "source_metadata_jsonl": source_metadata_jsonl,
            "output_jsonl": output_jsonl,
        }
    )
    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for row in annotations:
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
            "# R247 PromptNode Lifecycle Annotations",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Annotations: `{summary['annotations']}`",
            f"- Annotation types: `{summary['annotation_type_counts']}`",
            f"- Lifecycle actions: `{summary['lifecycle_action_counts']}`",
            f"- Edge actions: `{summary['edge_action_counts']}`",
            "",
            "## Boundary",
            "",
            "These annotations support lifecycle and mechanism discussion. They do not prove lifecycle-aware execution or accuracy improvement.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Annotate PromptNode lifecycle cases.")
    parser.add_argument("--decision_records_jsonl", required=True)
    parser.add_argument("--source_metadata_jsonl", required=True)
    parser.add_argument("--source_paths", nargs="+", required=True)
    parser.add_argument("--audit_paths", nargs="*", default=[])
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_lifecycle_annotation(
        decision_records_jsonl=args.decision_records_jsonl,
        source_metadata_jsonl=args.source_metadata_jsonl,
        source_paths=args.source_paths,
        audit_paths=args.audit_paths,
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
