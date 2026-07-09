from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_jsonl


def _safe_rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _count_options(question: str) -> int:
    return sum(1 for label in ("A", "B", "C", "D", "E") if f"Option {label}:" in question)


def build_subject_stats(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: {"records": 0, "correct": 0})
    for record in records:
        subject = str(record.get("subject") or "unknown")
        grouped[subject]["records"] += 1
        grouped[subject]["correct"] += int(bool(record.get("is_correct")))

    stats: Dict[str, Dict[str, Any]] = {}
    for subject, values in sorted(grouped.items()):
        records_count = values["records"]
        correct = values["correct"]
        stats[subject] = {
            "records": records_count,
            "correct": correct,
            "accuracy": _safe_rate(correct, records_count),
            "error_rate": _safe_rate(records_count - correct, records_count),
        }
    return stats


def load_contract_summary(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    raw_rate = float(summary.get("raw_contract_ready_rate") or 0.0)
    projected_rate = float(
        summary.get("projected_contract_ready_rate")
        or summary.get("projection_contract_ready_rate")
        or 0.0
    )
    return {
        "raw_contract_ready_rate": raw_rate,
        "projected_contract_ready_rate": projected_rate,
        "projection_gap": round(projected_rate - raw_rate, 6),
        "projection_audit_pass": bool(summary.get("projection_audit_pass")),
        "source_run_id": summary.get("run_id"),
    }


def build_transfer_feature_row(
    record: Dict[str, Any],
    subject_stats: Dict[str, Dict[str, Any]],
    contract_summary: Dict[str, Any],
) -> Dict[str, Any]:
    subject = str(record.get("subject") or "unknown")
    stats = subject_stats.get(
        subject,
        {"records": 0, "correct": 0, "accuracy": 0.0, "error_rate": 0.0},
    )
    predicted_answer = str(record.get("predicted_answer") or "").strip().upper()
    true_answer = str(record.get("true_answer") or "").strip().upper()
    is_correct = bool(record.get("is_correct"))

    features = {
        "subject": subject,
        "option_count": _count_options(str(record.get("question") or "")),
        "arg_prediction_valid": predicted_answer[:1] in {"A", "B", "C", "D", "E"},
        "subject_records": int(stats["records"]),
        "subject_arg_accuracy": float(stats["accuracy"]),
        "subject_arg_error_rate": float(stats["error_rate"]),
        "raw_contract_ready_rate": float(contract_summary.get("raw_contract_ready_rate") or 0.0),
        "projected_contract_ready_rate": float(
            contract_summary.get("projected_contract_ready_rate") or 0.0
        ),
        "projection_gap": float(contract_summary.get("projection_gap") or 0.0),
        "projection_audit_pass": bool(contract_summary.get("projection_audit_pass")),
    }
    labels = {
        "true_answer": true_answer,
        "predicted_answer": predicted_answer,
        "arg_correct": is_correct,
        "arg_error": not is_correct,
    }
    probe_priority = (
        "arg_error_transfer_probe" if labels["arg_error"] else "control_correct_transfer_probe"
    )
    return {
        "task_id": record.get("task_id"),
        "dataset": record.get("dataset", "mmlu"),
        "features": features,
        "labels": labels,
        "probe_priority": probe_priority,
        "model_visible_feature_keys": sorted(features.keys()),
        "label_keys_not_model_visible": sorted(labels.keys()),
    }


def summarize_transfer_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    priorities = Counter(row.get("probe_priority", "unknown") for row in rows)
    subjects = Counter(row.get("features", {}).get("subject", "unknown") for row in rows)
    error_subjects = Counter(
        row.get("features", {}).get("subject", "unknown")
        for row in rows
        if row.get("labels", {}).get("arg_error") is True
    )
    return {
        "rows": len(rows),
        "arg_errors": sum(1 for row in rows if row.get("labels", {}).get("arg_error") is True),
        "correct_controls": sum(
            1 for row in rows if row.get("labels", {}).get("arg_error") is False
        ),
        "probe_priorities": dict(sorted(priorities.items())),
        "subjects": dict(sorted(subjects.items())),
        "error_subjects": dict(sorted(error_subjects.items())),
    }


def run_transfer_feature_table(
    transfer_results_jsonl: str,
    contract_summary_json: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
) -> Dict[str, Any]:
    records = load_jsonl(transfer_results_jsonl)
    subject_stats = build_subject_stats(records)
    contract_summary = load_contract_summary(contract_summary_json)
    rows = [
        build_transfer_feature_row(record, subject_stats, contract_summary) for record in records
    ]
    summary = summarize_transfer_rows(rows)
    summary.update(
        {
            "run_id": "R248",
            "title": "MMLU transfer feature table",
            "claim_boundary": "No-API transfer feature table only. It identifies label-free probe features and ARG error candidates; it does not claim PromptNode/PromptEdge transfer accuracy improvement.",
            "no_api": True,
            "broad_api": False,
            "transfer_results_jsonl": transfer_results_jsonl,
            "contract_summary_json": contract_summary_json,
            "output_jsonl": output_jsonl,
            "subject_stats": subject_stats,
            "contract_summary": contract_summary,
            "feature_label_separation": "features are model-visible and exclude true_answer/predicted labels; labels are evaluation-only",
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
            "# R248 MMLU Transfer Feature Table",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Rows: `{summary['rows']}`",
            f"- ARG errors / correct controls: `{summary['arg_errors']}` / `{summary['correct_controls']}`",
            f"- Probe priorities: `{summary['probe_priorities']}`",
            f"- Error subjects: `{summary['error_subjects']}`",
            f"- Contract rates raw/projected: `{summary['contract_summary']['raw_contract_ready_rate']}` / `{summary['contract_summary']['projected_contract_ready_rate']}`",
            "",
            "## Boundary",
            "",
            "This table is a transfer-probe scaffold. It keeps labels out of model-visible features and should be used to select MMLU error/control probes before any API run.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export MMLU transfer feature table.")
    parser.add_argument("--transfer_results_jsonl", required=True)
    parser.add_argument("--contract_summary_json", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_transfer_feature_table(
        transfer_results_jsonl=args.transfer_results_jsonl,
        contract_summary_json=args.contract_summary_json,
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
