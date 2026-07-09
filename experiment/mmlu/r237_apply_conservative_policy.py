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
from experiment.mmlu.r236_conservative_abstention_policy import policy_switches


VALID_LABELS = {"A", "B", "C", "D", "E"}


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label.startswith("NONE"):
        return "NONE"
    return label[:1] if label[:1] in VALID_LABELS else "NONE"


def build_source_lookup(paths: List[str]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for path in paths:
        for row in load_jsonl(path):
            task_id = str(row.get("task_id") or "")
            true_answer = normalize_label(row.get("true_answer") or row.get("gold_answer"))
            if task_id and true_answer in VALID_LABELS and task_id not in lookup:
                lookup[task_id] = {
                    "task_id": task_id,
                    "true_answer": true_answer,
                    "question": row.get("question"),
                    "source_path": path,
                }
    return lookup


def _policy_input(row: Dict[str, Any]) -> Dict[str, Any]:
    return dict(row.get("model_visible_input") or {})


def apply_policy_to_manifest_row(
    row: Dict[str, Any],
    source_lookup: Dict[str, Dict[str, Any]],
    policy: str,
) -> Dict[str, Any]:
    task_id = str(row.get("task_id") or "")
    source = source_lookup.get(task_id, {})
    policy_input = _policy_input(row)
    baseline = normalize_label(policy_input.get("baseline_prediction"))
    objective = normalize_label(policy_input.get("objective_prediction"))
    true_answer = normalize_label(source.get("true_answer"))
    switch = policy_switches(policy, policy_input)
    selected = objective if switch else baseline
    baseline_correct = baseline == true_answer if true_answer in VALID_LABELS else None
    selected_correct = selected == true_answer if true_answer in VALID_LABELS else None
    return {
        "task_id": task_id,
        "split_role": row.get("split_role"),
        "policy": policy,
        "source_available": bool(source),
        "source_path": source.get("source_path"),
        "true_answer": true_answer,
        "baseline_prediction": baseline,
        "objective_prediction": objective,
        "selected_prediction": selected,
        "switch": switch,
        "objective_top_score": int(policy_input.get("objective_top_score") or 0),
        "baseline_direct_majority_count": int(policy_input.get("baseline_direct_majority_count") or 0),
        "baseline_correct": baseline_correct,
        "selected_correct": selected_correct,
        "fix": baseline_correct is False and selected_correct is True,
        "harm": baseline_correct is True and selected_correct is False,
    }


def summarize_policy_application(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    evaluated = [row for row in records if row.get("selected_correct") is not None]
    return {
        "records": len(records),
        "evaluated_records": len(evaluated),
        "source_missing": sum(1 for row in records if not row.get("source_available")),
        "switches": sum(1 for row in evaluated if row.get("switch")),
        "accuracy_count": sum(1 for row in evaluated if row.get("selected_correct")),
        "accuracy": (
            sum(1 for row in evaluated if row.get("selected_correct")) / len(evaluated)
            if evaluated
            else None
        ),
        "baseline_accuracy_count": sum(1 for row in evaluated if row.get("baseline_correct")),
        "fixes": sum(1 for row in evaluated if row.get("fix")),
        "harms": sum(1 for row in evaluated if row.get("harm")),
    }


def _split_summaries(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out = {"all": summarize_policy_application(records)}
    for split in sorted({str(row.get("split_role")) for row in records}):
        out[split] = summarize_policy_application([row for row in records if str(row.get("split_role")) == split])
    return out


def _r233_task_ids(path: str) -> set[str]:
    if not path:
        return set()
    return {str(row.get("task_id")) for row in load_jsonl(path) if row.get("control_variant") == "proposed_router_final"}


def run_policy_application(
    manifest_jsonl: str,
    source_paths: List[str],
    r233_results_jsonl: str,
    policy: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
) -> Dict[str, Any]:
    source_lookup = build_source_lookup(source_paths)
    manifest_rows = load_jsonl(manifest_jsonl)
    records = [apply_policy_to_manifest_row(row, source_lookup, policy) for row in manifest_rows]
    r233_ids = _r233_task_ids(r233_results_jsonl)
    r233_records = [row for row in records if row["task_id"] in r233_ids]
    summary = {
        "run_id": "R237",
        "title": "Apply conservative abstention policy",
        "claim_boundary": "Offline policy replay only; no API, no superiority claim, and no SCI-Q2 readiness claim.",
        "no_api": True,
        "policy": policy,
        "manifest_jsonl": manifest_jsonl,
        "source_paths": source_paths,
        "r233_results_jsonl": r233_results_jsonl,
        "output_jsonl": output_jsonl,
        "split_summaries": _split_summaries(records),
        "r233_subset": summarize_policy_application(r233_records),
    }
    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def _metric_line(item: Dict[str, Any]) -> str:
    return (
        f"`{item['accuracy_count']}/{item['evaluated_records']}` acc, "
        f"`{item['fixes']}/{item['harms']}` fix/harm, "
        f"`{item['switches']}` switches, source missing `{item['source_missing']}`"
    )


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R237 Conservative Policy Application",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"Policy: `{summary['policy']}`",
        "",
        "## Split Results",
        "",
        "| Split | Metrics |",
        "|---|---|",
    ]
    for split, item in summary["split_summaries"].items():
        rows.append(f"| `{split}` | {_metric_line(item)} |")
    rows.extend(
        [
            "",
            "## R233 Subset",
            "",
            _metric_line(summary["r233_subset"]),
            "",
            "## Interpretation",
            "",
            "The conservative policy should be judged as an offline replay, not a new model result. Its purpose is to verify that the abstention boundary learned from R234 eliminates the observed clean harm before any future API run.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply conservative policy to router-final manifests.")
    parser.add_argument("--manifest_jsonl", required=True)
    parser.add_argument("--source_paths", nargs="+", required=True)
    parser.add_argument("--r233_results_jsonl", default="")
    parser.add_argument("--policy", default="baseline_consensus_guard_top3")
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_policy_application(
        manifest_jsonl=args.manifest_jsonl,
        source_paths=args.source_paths,
        r233_results_jsonl=args.r233_results_jsonl,
        policy=args.policy,
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
