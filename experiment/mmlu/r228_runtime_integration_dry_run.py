from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r222_control_manifest_leakage_scan import scan_control_rows


REQUIRED_FIELDS = [
    "task_id",
    "control_variant",
    "baseline_answer",
    "router_final_answer",
    "would_switch",
    "selected_label",
    "fallback_reason",
    "leakage_pass",
]
VALID_LABELS = {"A", "B", "C", "D", "E"}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _baseline_answer(row: Dict[str, Any]) -> str:
    label = str(row.get("model_visible_input", {}).get("baseline_prediction") or "NONE").strip().upper()
    return label if label in VALID_LABELS else "NONE"


def _allowed_labels(row: Dict[str, Any]) -> set[str]:
    labels = row.get("router_final_schema", {}).get("allowed_option_labels", [])
    return {str(label).strip().upper() for label in labels}


def build_integration_record(row: Dict[str, Any]) -> Dict[str, Any]:
    leakage = scan_control_rows([row])
    baseline_answer = _baseline_answer(row)
    control_variant = row.get("control_variant", "proposed_router_final")
    target_label = str(row.get("target_option_label") or "NONE").strip().upper()
    allowed = _allowed_labels(row) or (VALID_LABELS | {"NONE"})

    would_switch = False
    selected_label = "NONE"
    router_final_answer = baseline_answer
    fallback_reason = "router_abstain"

    if control_variant == "cost_matched_arg_requery":
        fallback_reason = "cost_matched_arg_requery"
    elif not leakage["leakage_pass"]:
        fallback_reason = "leakage_rejected"
    elif row.get("router_action") == "switch_to_objective" and target_label in VALID_LABELS and target_label in allowed:
        would_switch = True
        selected_label = target_label
        router_final_answer = target_label
        fallback_reason = "router_switch"
    elif row.get("router_action") == "switch_to_objective":
        fallback_reason = "invalid_target_label"

    return {
        "task_id": row.get("task_id"),
        "split_role": row.get("split_role"),
        "control_variant": control_variant,
        "baseline_answer": baseline_answer,
        "router_final_answer": router_final_answer,
        "would_switch": would_switch,
        "selected_label": selected_label,
        "fallback_reason": fallback_reason,
        "leakage_pass": leakage["leakage_pass"],
        "leakage_violations": leakage["leakage_violations"],
        "api_executed": False,
        "cost": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }


def summarize_integration_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    missing = 0
    for row in records:
        missing += sum(1 for field in REQUIRED_FIELDS if field not in row)
    return {
        "records": len(records),
        "would_switch": sum(1 for row in records if row.get("would_switch")),
        "leakage_violations": sum(int(row.get("leakage_violations", 0)) for row in records),
        "missing_required_fields": missing,
        "variant_counts": dict(sorted(Counter(row.get("control_variant", "") for row in records).items())),
        "fallback_reasons": dict(sorted(Counter(row.get("fallback_reason", "") for row in records).items())),
    }


def run_integration_dry_run(input_paths: List[str], output_jsonl: str, summary_json: str, report_md: str) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    path_counts: Dict[str, int] = {}
    for path in input_paths:
        rows = load_jsonl(path)
        path_counts[path] = len(rows)
        records.extend(build_integration_record(row) for row in rows)

    summary = summarize_integration_records(records)
    summary.update(
        {
            "run_id": "R228",
            "title": "Runtime integration dry-run",
            "claim_boundary": "Integration dry-run only; no API and no accuracy claim.",
            "no_api": True,
            "input_paths": input_paths,
            "input_path_counts": path_counts,
            "output_jsonl": output_jsonl,
        }
    )

    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for row in records:
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
            "# R228 Runtime Integration Dry-Run",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Input files: `{len(summary['input_paths'])}`",
            f"- Records: `{summary['records']}`",
            f"- Would switch: `{summary['would_switch']}`",
            f"- Leakage violations: `{summary['leakage_violations']}`",
            f"- Missing required fields: `{summary['missing_required_fields']}`",
            f"- Variants: `{summary['variant_counts']}`",
            f"- Fallback reasons: `{summary['fallback_reasons']}`",
            "",
            "## Boundary",
            "",
            "This dry-run validates local decision logging only. It does not run an LLM or compare correctness.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run router-final runtime integration.")
    parser.add_argument("--input_paths", nargs="+", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    expanded: List[str] = []
    for pattern in args.input_paths:
        matches = sorted(glob.glob(pattern))
        expanded.extend(matches or [pattern])
    summary = run_integration_dry_run(
        input_paths=expanded,
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
