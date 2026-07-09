import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


FORBIDDEN_POLICY_INPUT_FIELDS = [
    "true_answer",
    "is_solved",
    "baseline_is_solved",
    "clean_label",
    "audit_label",
    "task_id",
]
RULE_NAME = "r076_clean_fix_preserving_policy_targets"


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_json(path: str, payload: Dict[str, Any]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, records: Iterable[Dict[str, Any]]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _absolute(path: str) -> str:
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(REPO_ROOT, path))


def _by_task(path: str) -> Dict[str, Dict[str, Any]]:
    return {str(record["task_id"]): record for record in load_jsonl(_absolute(path))}


def _audit_labels(path: str) -> Dict[str, str]:
    labels = {}
    for record in load_jsonl(_absolute(path)):
        labels[str(record["task_id"])] = str(record.get("clean_label") or "unknown")
    return labels


def _sanitized_features(record: Dict[str, Any]) -> Dict[str, Any]:
    features = dict(record.get("trigger_features") or {})
    for field in FORBIDDEN_POLICY_INPUT_FIELDS:
        features.pop(field, None)
    features.pop("baseline_prediction", None)
    features.pop("direct_votes", None)
    features.pop("direct_vote_counts", None)
    features.pop("direct_distinct_options", None)
    return features


def _recommended_policy(task_id: str, target_class: str) -> str:
    if task_id == "task_188":
        return "run_on_direct_conflict_with_alternative_vote"
    if task_id == "task_56":
        return "require_three_view_support_for_invalid_or_missing_vote"
    if task_id == "task_8":
        return "full_multiview_objective_on_low_coverage_missing_votes"
    if target_class == "noisy_optional":
        return "noisy_optional_do_not_train_as_clean_positive"
    return "suppress_unstable_switch"


def _target_row(
    task_id: str,
    target_class: str,
    audit_label: str,
    r069: Dict[str, Any],
    r072: Dict[str, Any],
    r074: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "target_class": target_class,
        "recommended_policy": _recommended_policy(task_id, target_class),
        "policy_input": {
            "r072_trigger_features": _sanitized_features(r072) if r072 else {},
            "r074_trigger_features": _sanitized_features(r074) if r074 else {},
            "r074_trigger_policy": "r073_surgical",
        },
        "distillation_evidence": {
            "audit_label": audit_label,
            "r069_fixed": bool(r069 and (not r069.get("baseline_is_solved")) and r069.get("is_solved")),
            "r072_fixed": bool(r072 and (not r072.get("baseline_is_solved")) and r072.get("is_solved")),
            "r074_fixed": bool(r074 and (not r074.get("baseline_is_solved")) and r074.get("is_solved")),
            "r072_view_calls": r072.get("view_calls") if r072 else None,
            "r074_view_calls": r074.get("view_calls") if r074 else None,
            "r072_view_predictions": r072.get("view_predictions", {}) if r072 else {},
            "r074_view_predictions": r074.get("view_predictions", {}) if r074 else {},
        },
    }


def build_clean_fix_policy_targets(
    r069_path: str = "experiment/aqua/aqua_tail34_r069_integrated_selective_multiview_results.jsonl",
    r072_path: str = "experiment/aqua/aqua_tail34_r072_integrated_cascade_results.jsonl",
    r074_path: str = "experiment/aqua/aqua_tail34_r074_surgical_cascade_results.jsonl",
    audit_path: str = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    r069_records = _by_task(r069_path)
    r072_records = _by_task(r072_path)
    r074_records = _by_task(r074_path)
    audit_labels = _audit_labels(audit_path)

    clean_positive = set()
    noisy_optional = set()
    unstable_boundary = set()
    for task_id in sorted(set(r069_records) | set(r072_records) | set(r074_records)):
        audit_label = audit_labels.get(task_id, "unknown")
        fixed_by_clean_run = any(
            records.get(task_id)
            and (not records[task_id].get("baseline_is_solved"))
            and records[task_id].get("is_solved")
            for records in [r069_records, r072_records]
        )
        fixed_by_r074 = (
            r074_records.get(task_id)
            and (not r074_records[task_id].get("baseline_is_solved"))
            and r074_records[task_id].get("is_solved")
        )
        switched_without_fix = (
            r074_records.get(task_id)
            and r074_records[task_id].get("selected_source") == "cascade_objective"
            and not r074_records[task_id].get("is_solved")
        )
        if fixed_by_clean_run and audit_label == "clean":
            clean_positive.add(task_id)
        elif fixed_by_r074 and audit_label != "clean":
            noisy_optional.add(task_id)
        elif switched_without_fix:
            unstable_boundary.add(task_id)

    rows = []
    for task_id in sorted(clean_positive):
        rows.append(
            _target_row(
                task_id,
                "clean_fix_preserve",
                audit_labels.get(task_id, "unknown"),
                r069_records.get(task_id, {}),
                r072_records.get(task_id, {}),
                r074_records.get(task_id, {}),
            )
        )
    for task_id in sorted(noisy_optional):
        rows.append(
            _target_row(
                task_id,
                "noisy_optional",
                audit_labels.get(task_id, "unknown"),
                r069_records.get(task_id, {}),
                r072_records.get(task_id, {}),
                r074_records.get(task_id, {}),
            )
        )
    for task_id in sorted(unstable_boundary - clean_positive - noisy_optional):
        rows.append(
            _target_row(
                task_id,
                "unstable_switch_boundary",
                audit_labels.get(task_id, "unknown"),
                r069_records.get(task_id, {}),
                r072_records.get(task_id, {}),
                r074_records.get(task_id, {}),
            )
        )

    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_targets": len(rows),
        "clean_positive_tasks": sorted(clean_positive),
        "noisy_optional_tasks": sorted(noisy_optional),
        "unstable_boundary_tasks": sorted(unstable_boundary - clean_positive - noisy_optional),
        "forbidden_policy_input_fields": FORBIDDEN_POLICY_INPUT_FIELDS,
        "claim_boundary": "Distillation target export only; not a new answer-accuracy result.",
    }
    return rows, summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R076 Clean-Fix-Preserving Policy Targets",
            "",
            "## Summary",
            "",
            f"- Clean positive tasks: `{', '.join(summary['clean_positive_tasks'])}`",
            f"- Noisy optional tasks: `{', '.join(summary['noisy_optional_tasks'])}`",
            f"- Unstable boundary tasks: `{', '.join(summary['unstable_boundary_tasks'])}`",
            "",
            "These rows are training/selector targets, not a new accuracy result. Policy inputs exclude true answers, correctness fields, audit labels, and task ids.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export clean-fix-preserving selector targets.")
    parser.add_argument(
        "--output-file",
        default="experiment/aqua/aqua_tail34_r076_clean_fix_policy_targets.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_tail34_r076_clean_fix_policy_targets_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_tail34_r076_clean_fix_policy_targets_report.md",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows, summary = build_clean_fix_policy_targets()
    write_jsonl(_absolute(args.output_file), rows)
    write_json(_absolute(args.summary_json), summary)
    write_text(_absolute(args.report_md), render_report(summary))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
