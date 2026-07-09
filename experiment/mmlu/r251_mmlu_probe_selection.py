from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_jsonl


def _subject(row: Dict[str, Any]) -> str:
    return str(row.get("features", {}).get("subject") or "unknown")


def _is_arg_error(row: Dict[str, Any]) -> bool:
    return row.get("labels", {}).get("arg_error") is True


def _sorted_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda row: (_subject(row), str(row.get("task_id") or "")))


def _take_diverse_errors(
    errors: List[Dict[str, Any]],
    max_error_rows: Optional[int],
) -> List[Dict[str, Any]]:
    sorted_errors = _sorted_rows(errors)
    if max_error_rows is None or len(sorted_errors) <= max_error_rows:
        return sorted_errors

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in sorted_errors:
        grouped[_subject(row)].append(row)

    selected: List[Dict[str, Any]] = []
    while len(selected) < max_error_rows:
        progressed = False
        for subject in sorted(grouped):
            if grouped[subject] and len(selected) < max_error_rows:
                selected.append(grouped[subject].pop(0))
                progressed = True
        if not progressed:
            break
    return selected


def select_subject_matched_controls(
    errors: List[Dict[str, Any]],
    controls: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    needed = Counter(_subject(row) for row in errors)
    grouped_controls: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in _sorted_rows(controls):
        grouped_controls[_subject(row)].append(row)

    selected: List[Dict[str, Any]] = []
    for subject, count in sorted(needed.items()):
        available = grouped_controls.get(subject, [])
        selected.extend(available[:count])
    return selected


def _mark(row: Dict[str, Any], role: str) -> Dict[str, Any]:
    out = dict(row)
    out["selection_role"] = role
    out["selection_reason"] = (
        "ARG baseline error selected for transfer probe"
        if role == "arg_error"
        else "Subject-matched ARG-correct control"
    )
    return out


def build_balanced_probe_rows(
    feature_rows: List[Dict[str, Any]],
    max_error_rows: Optional[int] = None,
) -> List[Dict[str, Any]]:
    errors = _take_diverse_errors([row for row in feature_rows if _is_arg_error(row)], max_error_rows)
    controls = [row for row in feature_rows if not _is_arg_error(row)]
    matched_controls = select_subject_matched_controls(errors, controls)
    return [_mark(row, "arg_error") for row in errors] + [
        _mark(row, "matched_control") for row in matched_controls
    ]


def summarize_probe_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    role_counts = Counter(row.get("selection_role", "unknown") for row in rows)
    subject_counts = Counter(_subject(row) for row in rows)
    subject_role_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"arg_error": 0, "matched_control": 0})
    for row in rows:
        role = row.get("selection_role", "unknown")
        if role in {"arg_error", "matched_control"}:
            subject_role_counts[_subject(row)][role] += 1
    return {
        "rows": len(rows),
        "role_counts": dict(sorted(role_counts.items())),
        "subjects": dict(sorted(subject_counts.items())),
        "subject_role_counts": dict(sorted((k, dict(v)) for k, v in subject_role_counts.items())),
        "balanced_error_control": role_counts.get("arg_error", 0)
        == role_counts.get("matched_control", 0),
        "subjects_with_errors": sorted(
            subject for subject, counts in subject_role_counts.items() if counts["arg_error"] > 0
        ),
    }


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_probe_selection(
    feature_table_jsonl: str,
    output_jsonl: str,
    tiny_output_jsonl: str,
    summary_json: str,
    report_md: str,
    tiny_error_cap: int,
) -> Dict[str, Any]:
    feature_rows = load_jsonl(feature_table_jsonl)
    full_rows = build_balanced_probe_rows(feature_rows)
    tiny_rows = build_balanced_probe_rows(feature_rows, max_error_rows=tiny_error_cap)
    full_summary = summarize_probe_rows(full_rows)
    tiny_summary = summarize_probe_rows(tiny_rows)
    summary = {
        "run_id": "R251",
        "title": "MMLU transfer probe selection",
        "claim_boundary": "Probe selection only; no API, no transfer accuracy claim, and no SCI-Q2 readiness claim.",
        "no_api": True,
        "broad_api": False,
        "feature_table_jsonl": feature_table_jsonl,
        "output_jsonl": output_jsonl,
        "tiny_output_jsonl": tiny_output_jsonl,
        "tiny_error_cap": tiny_error_cap,
        "full24": full_summary,
        "tiny16": tiny_summary,
        "selection_policy": "full set uses all ARG errors with same-subject controls; tiny set uses subject-diverse ARG errors with same-subject controls",
    }
    _write_jsonl(output_jsonl, full_rows)
    _write_jsonl(tiny_output_jsonl, tiny_rows)
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
            "# R251 MMLU Transfer Probe Selection",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Full set rows: `{summary['full24']['rows']}`; roles: `{summary['full24']['role_counts']}`",
            f"- Tiny set rows: `{summary['tiny16']['rows']}`; roles: `{summary['tiny16']['role_counts']}`",
            f"- Tiny subjects: `{summary['tiny16']['subjects_with_errors']}`",
            "",
            "## Boundary",
            "",
            "This run only selects probes. It does not execute any model and does not support a transfer-improvement claim.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select MMLU transfer probe rows.")
    parser.add_argument("--feature_table_jsonl", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--tiny_output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--tiny_error_cap", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_probe_selection(
        feature_table_jsonl=args.feature_table_jsonl,
        output_jsonl=args.output_jsonl,
        tiny_output_jsonl=args.tiny_output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
        tiny_error_cap=args.tiny_error_cap,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
