import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.objective_safety_proxy_protocol import REQUIRED_RULE_FEATURES  # noqa: E402
from experiment.aqua.objective_safety_rule_distillation import _distilled_action  # noqa: E402
from experiment.aqua.offline_utility_selector import extract_contract_consensus_features  # noqa: E402


RULE_NAME = "r112_first200_objective_safety_feature_export"
CLAIM_BOUNDARY = (
    "first200 feature export and proxy target construction only; no trained proxy or accuracy claim"
)

DEFAULT_BASELINE_SOURCES = [
    "experiment/aqua/aqua_100_arg_baseline_results.jsonl",
    "experiment/aqua/aqua_next100_arg_baseline_results.jsonl",
]
DEFAULT_OBJECTIVE_SOURCE = "experiment/aqua/aqua_first200_objective_guided_selector_results.jsonl"
DEFAULT_TARGET_JSONL = "experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_first200_r112_objective_safety_feature_export_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_first200_r112_objective_safety_feature_export_report.md"
)

FORBIDDEN_POLICY_INPUT_FIELDS = {
    "task_id",
    "true_answer",
    "is_solved",
    "baseline_is_solved",
    "objective_selector_is_solved",
    "safety_composed_is_solved",
    "clean_label",
    "audit_label",
    "gold_binding_status",
    "rationale_issue",
    "target_action",
    "target_reason",
}


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _load_baseline_records(paths: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    for path in paths:
        for record in _load_jsonl(path):
            task_id = record["task_id"]
            if task_id in records:
                raise ValueError(f"Duplicate baseline task_id in first200 sources: {task_id}")
            records[task_id] = record
    return records


def _write_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _policy_input_from_records(
    baseline_record: Dict[str, Any],
    objective_record: Dict[str, Any],
) -> Dict[str, Any]:
    baseline_features = extract_contract_consensus_features(baseline_record)
    direct_valid = int(baseline_features.get("direct_valid_vote_count") or 0)
    direct_majority = int(baseline_features.get("direct_majority_count") or 0)
    objective_prediction = objective_record.get("predicted_answer")
    baseline_prediction = baseline_record.get("predicted_answer")
    return {
        "baseline_prediction": baseline_prediction,
        "objective_prediction": objective_prediction,
        "objective_prediction_differs_from_baseline": objective_prediction != baseline_prediction,
        "objective_selected_source": objective_record.get("selected_source"),
        "objective_top_score": int(objective_record.get("top_score") or 0),
        "baseline_direct_majority": baseline_features.get("direct_majority"),
        "baseline_direct_majority_count": direct_majority,
        "baseline_direct_valid_vote_count": direct_valid,
        "baseline_direct_votes_split": direct_valid > direct_majority,
    }


def _target_reason(policy_input: Dict[str, Any], target_action: str) -> str:
    if not policy_input["objective_prediction_differs_from_baseline"]:
        return "same_prediction_as_arg"
    if target_action == "switch_to_objective" and int(policy_input["objective_top_score"]) >= 3:
        return "objective_top_score_ge3"
    if target_action == "switch_to_objective" and bool(policy_input["baseline_direct_votes_split"]):
        return "baseline_direct_split_allows_switch"
    return "insufficient_safety_evidence"


def build_first200_feature_export(
    baseline_sources: Sequence[str] = DEFAULT_BASELINE_SOURCES,
    objective_source: str = DEFAULT_OBJECTIVE_SOURCE,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    baseline = _load_baseline_records(baseline_sources)
    objective_records = _load_jsonl(objective_source)
    objective_task_ids = {record["task_id"] for record in objective_records}
    if len(objective_task_ids) != len(objective_records):
        raise ValueError("Duplicate task_id in first200 objective source")

    rows: List[Dict[str, Any]] = []
    baseline_prediction_mismatches = 0
    for objective_record in objective_records:
        task_id = objective_record["task_id"]
        if task_id not in baseline:
            raise ValueError(f"Missing baseline record for objective task: {task_id}")
        baseline_record = baseline[task_id]
        policy_input = _policy_input_from_records(baseline_record, objective_record)
        if objective_record.get("baseline_prediction") != baseline_record.get("predicted_answer"):
            baseline_prediction_mismatches += 1
        target_action = _distilled_action(policy_input)
        rows.append(
            {
                "task_id": task_id,
                "slice_prefix": objective_record.get("slice_prefix"),
                "policy_input": policy_input,
                "target_action": target_action,
                "target_reason": _target_reason(policy_input, target_action),
                "target_prediction_source": (
                    "objective" if target_action == "switch_to_objective" else "arg_baseline"
                ),
                "source_run": "first200_r112_feature_export",
            }
        )

    exported_features = [
        feature
        for feature in REQUIRED_RULE_FEATURES
        if all(feature in row["policy_input"] for row in rows)
    ]
    missing_features = [
        feature for feature in REQUIRED_RULE_FEATURES if feature not in exported_features
    ]
    target_actions = Counter(row["target_action"] for row in rows)
    target_reasons = Counter(row["target_reason"] for row in rows)
    switch_rows = [row for row in rows if row["target_action"] == "switch_to_objective"]
    source_paths = [*baseline_sources, objective_source]
    summary = {
        "rule": RULE_NAME,
        "baseline_sources": list(baseline_sources),
        "objective_source": objective_source,
        "target_jsonl": DEFAULT_TARGET_JSONL,
        "num_rows": len(rows),
        "baseline_source_rows": len(baseline),
        "objective_source_rows": len(objective_records),
        "baseline_prediction_mismatch_count": baseline_prediction_mismatches,
        "required_rule_features": list(REQUIRED_RULE_FEATURES),
        "required_rule_feature_count": len(REQUIRED_RULE_FEATURES),
        "exported_required_rule_features": exported_features,
        "missing_required_rule_features": missing_features,
        "uses_tail34_training_source": any("tail34" in path for path in source_paths),
        "policy_input_field_violations": sum(
            1
            for row in rows
            if FORBIDDEN_POLICY_INPUT_FIELDS.intersection(row["policy_input"])
        ),
        "target_action_counts": dict(sorted(target_actions.items())),
        "target_reason_counts": dict(sorted(target_reasons.items())),
        "objective_prediction_differs_count": sum(
            1
            for row in rows
            if row["policy_input"]["objective_prediction_differs_from_baseline"]
        ),
        "baseline_direct_votes_split_count": sum(
            1 for row in rows if row["policy_input"]["baseline_direct_votes_split"]
        ),
        "switch_target_count": len(switch_rows),
        "switch_target_tasks": [row["task_id"] for row in switch_rows],
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return rows, summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R112 First200 Objective-Safety Feature Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Rows: `{summary['num_rows']}`",
            f"- Baseline source rows: `{summary['baseline_source_rows']}`",
            f"- Objective source rows: `{summary['objective_source_rows']}`",
            f"- Required rule features: `{summary['required_rule_features']}`",
            f"- Exported required features: `{summary['exported_required_rule_features']}`",
            f"- Missing required features: `{summary['missing_required_rule_features']}`",
            f"- Uses tail34 training source: `{summary['uses_tail34_training_source']}`",
            f"- Policy-input field violations: `{summary['policy_input_field_violations']}`",
            f"- Baseline-prediction mismatches: `{summary['baseline_prediction_mismatch_count']}`",
            f"- Target actions: `{summary['target_action_counts']}`",
            f"- Target reasons: `{summary['target_reason_counts']}`",
            f"- Objective differs count: `{summary['objective_prediction_differs_count']}`",
            f"- Baseline direct-votes split count: `{summary['baseline_direct_votes_split_count']}`",
            f"- Switch target tasks: `{summary['switch_target_tasks']}`",
            "",
            "## Interpretation",
            "",
            "R112 supplies the missing first200/non-tail34 inputs required by the R110 proxy protocol. "
            "It reconstructs ARG direct-vote split from the two first200 ARG baseline slices and joins it "
            "with first200 objective-guided selector traces. The resulting rows can train or validate a "
            "proxy for the R109 objective-safety rule without using tail34 training data.",
            "",
            "This is not a trained proxy, a held-out accuracy result, or evidence that the method exceeds ARG. "
            "The next gate is to train or fit a proxy only on these non-tail34 rows and evaluate agreement on "
            "the frozen R109 tail34 targets.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export first200 objective-safety proxy features.")
    parser.add_argument("--target-jsonl", default=DEFAULT_TARGET_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows, summary = build_first200_feature_export()
    summary["target_jsonl"] = args.target_jsonl
    _write_jsonl(args.target_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R112 first200 objective-safety feature export: "
        f"rows={summary['num_rows']} switches={summary['switch_target_count']}"
    )


if __name__ == "__main__":
    main()
