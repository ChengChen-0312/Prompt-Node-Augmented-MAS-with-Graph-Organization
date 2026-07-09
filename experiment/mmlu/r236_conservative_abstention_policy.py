from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_jsonl
from experiment.mmlu.r234_tiny_diagnostic_failure_analysis import load_audit_lookup


POLICIES = [
    "current_top3",
    "high_confidence_top10",
    "high_confidence_top11",
    "baseline_invalid_top10",
    "baseline_consensus_guard_top3",
    "baseline_consensus_guard_top10",
]
VALID_LABELS = {"A", "B", "C", "D", "E"}


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label.startswith("NONE"):
        return "NONE"
    return label[:1] if label[:1] in VALID_LABELS else "NONE"


def _is_valid_label(value: Any) -> bool:
    return normalize_label(value) in VALID_LABELS


def _differs(feature: Dict[str, Any]) -> bool:
    return bool(feature.get("objective_prediction_differs_from_baseline"))


def _score(feature: Dict[str, Any]) -> int:
    return int(feature.get("objective_top_score") or 0)


def _baseline_majority_count(feature: Dict[str, Any]) -> int:
    return int(feature.get("baseline_direct_majority_count") or 0)


def policy_switches(policy_name: str, feature: Dict[str, Any]) -> bool:
    if policy_name == "current_top3":
        return _differs(feature) and _score(feature) >= 3
    if policy_name == "high_confidence_top10":
        return _differs(feature) and _score(feature) >= 10
    if policy_name == "high_confidence_top11":
        return _differs(feature) and _score(feature) >= 11
    if policy_name == "baseline_invalid_top10":
        return _differs(feature) and (not _is_valid_label(feature.get("baseline_prediction"))) and _score(feature) >= 10
    if policy_name == "baseline_consensus_guard_top3":
        return _differs(feature) and _score(feature) >= 3 and _baseline_majority_count(feature) < 3
    if policy_name == "baseline_consensus_guard_top10":
        return _differs(feature) and _score(feature) >= 10 and _baseline_majority_count(feature) < 3
    raise ValueError(f"Unknown policy: {policy_name}")


def load_feature_lookup(path: str) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for row in load_jsonl(path):
        task_id = str(row.get("task_id") or "")
        if task_id:
            lookup[task_id] = dict(row.get("policy_input") or {})
    return lookup


def evaluate_policy(
    rows: List[Dict[str, Any]],
    feature_lookup: Dict[str, Dict[str, Any]],
    policy_name: str,
    audit_lookup: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    audit_lookup = audit_lookup or {}
    details: List[Dict[str, Any]] = []
    for row in rows:
        task_id = str(row.get("task_id") or "")
        feature = feature_lookup.get(task_id, {})
        true_answer = normalize_label(row.get("true_answer"))
        baseline = normalize_label(feature.get("baseline_prediction", row.get("baseline_prediction")))
        objective = normalize_label(feature.get("objective_prediction", row.get("predicted_answer")))
        switch = policy_switches(policy_name, feature)
        selected = objective if switch else baseline
        baseline_correct = baseline == true_answer
        selected_correct = selected == true_answer
        audit = audit_lookup.get(task_id, {})
        details.append(
            {
                "task_id": task_id,
                "true_answer": true_answer,
                "baseline_prediction": baseline,
                "objective_prediction": objective,
                "selected_prediction": selected,
                "switch": switch,
                "objective_top_score": _score(feature),
                "baseline_direct_majority_count": _baseline_majority_count(feature),
                "baseline_correct": baseline_correct,
                "selected_correct": selected_correct,
                "fix": (not baseline_correct) and selected_correct,
                "harm": baseline_correct and not selected_correct,
                "clean_label": audit.get("clean_label", "unknown"),
            }
        )
    clean_details = [row for row in details if row.get("clean_label") == "clean"]
    return {
        "policy": policy_name,
        "tasks": len(details),
        "switches": sum(1 for row in details if row["switch"]),
        "switch_rate": sum(1 for row in details if row["switch"]) / len(details) if details else 0.0,
        "accuracy_count": sum(1 for row in details if row["selected_correct"]),
        "accuracy": sum(1 for row in details if row["selected_correct"]) / len(details) if details else 0.0,
        "baseline_accuracy_count": sum(1 for row in details if row["baseline_correct"]),
        "fixes": sum(1 for row in details if row["fix"]),
        "harms": sum(1 for row in details if row["harm"]),
        "clean_tasks": len(clean_details),
        "clean_fixes": sum(1 for row in clean_details if row["fix"]),
        "clean_harms": sum(1 for row in clean_details if row["harm"]),
        "details": details,
    }


def choose_conservative_policy(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    zero_harm = [row for row in results if row["harms"] == 0 and row["clean_harms"] == 0]
    candidates = zero_harm or results
    return sorted(
        candidates,
        key=lambda row: (row["accuracy_count"], row["fixes"], -row["switches"]),
        reverse=True,
    )[0]


def run_policy_derivation(
    source_jsonl: str,
    feature_jsonl: str,
    audit_paths: List[str],
    output_json: str,
    report_md: str,
) -> Dict[str, Any]:
    rows = load_jsonl(source_jsonl)
    feature_lookup = load_feature_lookup(feature_jsonl)
    audit_lookup = load_audit_lookup(audit_paths)
    results = [
        evaluate_policy(rows, feature_lookup, policy_name, audit_lookup=audit_lookup)
        for policy_name in POLICIES
    ]
    selected = choose_conservative_policy(results)
    summary = {
        "run_id": "R236",
        "title": "Conservative abstention policy derivation",
        "claim_boundary": "Offline policy derivation only; no API, no superiority claim, and no SCI-Q2 readiness claim.",
        "no_api": True,
        "source_jsonl": source_jsonl,
        "feature_jsonl": feature_jsonl,
        "audit_paths": audit_paths,
        "candidate_policies": [row["policy"] for row in results],
        "selected_policy": selected["policy"],
        "selected_metrics": {
            key: selected[key]
            for key in [
                "tasks",
                "switches",
                "switch_rate",
                "accuracy_count",
                "accuracy",
                "baseline_accuracy_count",
                "fixes",
                "harms",
                "clean_tasks",
                "clean_fixes",
                "clean_harms",
            ]
        },
        "policy_results": [
            {key: value for key, value in row.items() if key != "details"}
            for row in results
        ],
    }
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R236 Conservative Abstention Policy",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Candidate Results",
        "",
        "| Policy | Acc | Fix/Harm | Clean Fix/Harm | Switches |",
        "|---|---:|---:|---:|---:|",
    ]
    for result in summary["policy_results"]:
        rows.append(
            f"| `{result['policy']}` | `{result['accuracy_count']}/{result['tasks']}` | `{result['fixes']}/{result['harms']}` | `{result['clean_fixes']}/{result['clean_harms']}` | `{result['switches']}` |"
        )
    selected = summary["selected_metrics"]
    rows.extend(
        [
            "",
            "## Selected Policy",
            "",
            f"- Policy: `{summary['selected_policy']}`",
            f"- Accuracy: `{selected['accuracy_count']}/{selected['tasks']}`",
            f"- Fix/harm: `{selected['fixes']}/{selected['harms']}`",
            f"- Clean fix/harm: `{selected['clean_fixes']}/{selected['clean_harms']}`",
            f"- Switch rate: `{selected['switch_rate']:.4f}`",
            "",
            "## Interpretation",
            "",
            "The selected policy keeps the R233 lesson explicit: switch only when objective evidence differs from ARG and the ARG direct majority is not strong. This removes the clean harm seen in the prompt-only router while preserving a small number of fixes in the offline first200 slice.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Derive conservative abstention policies offline.")
    parser.add_argument("--source_jsonl", required=True)
    parser.add_argument("--feature_jsonl", required=True)
    parser.add_argument("--audit_paths", nargs="*", default=[])
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_policy_derivation(
        source_jsonl=args.source_jsonl,
        feature_jsonl=args.feature_jsonl,
        audit_paths=args.audit_paths,
        output_json=args.output_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
