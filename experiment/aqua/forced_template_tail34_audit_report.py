import argparse
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r093_forced_template_tail34_clean_noisy_audit"
CLAIM_BOUNDARY = "clean/noisy audit of R092 full forced-template validation, not a new method"

DEFAULT_R092_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r092_bad_exact_gate_forced_tail34_summary.json"
DEFAULT_AUDIT_JSONL = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r093_forced_template_clean_noisy_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r093_forced_template_clean_noisy_audit_report.md"


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_audit_by_task(path: str) -> Dict[str, Dict[str, Any]]:
    rows = {}
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                rows[record["task_id"]] = record
    return rows


def _fix_harm(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "fix": sum(
            1 for row in rows if not row["baseline_is_solved"] and row["gate_is_solved"]
        ),
        "harm": sum(
            1 for row in rows if row["baseline_is_solved"] and not row["gate_is_solved"]
        ),
    }


def _bucket_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "num_tasks": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "forced_template_solved": sum(1 for row in rows if row["forced_template_is_solved"]),
        "gate_solved": sum(1 for row in rows if row["gate_is_solved"]),
        "fix_harm": _fix_harm(rows),
        "fix_tasks": [
            row["task_id"] for row in rows if not row["baseline_is_solved"] and row["gate_is_solved"]
        ],
        "harm_tasks": [
            row["task_id"] for row in rows if row["baseline_is_solved"] and not row["gate_is_solved"]
        ],
    }


def build_tail34_audit_summary(
    r092_summary_json: str = DEFAULT_R092_SUMMARY_JSON,
    audit_jsonl: str = DEFAULT_AUDIT_JSONL,
) -> Dict[str, Any]:
    r092 = _load_json(r092_summary_json)
    audits = _load_audit_by_task(audit_jsonl)
    rows = []
    for row in r092["rows"]:
        audit = audits[row["task_id"]]
        enriched = dict(row)
        enriched.update(
            {
                "clean_label": audit.get("clean_label", "unknown"),
                "gold_binding_status": audit.get("gold_binding_status", "unknown"),
                "rationale_issue": audit.get("rationale_issue", "unknown"),
                "faithful_answer": audit.get("faithful_answer", "UNKNOWN"),
                "audit_confidence": audit.get("confidence", "unknown"),
                "audit_reason": audit.get("brief_reason", ""),
            }
        )
        rows.append(enriched)

    by_label: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_label.setdefault(row["clean_label"], []).append(row)

    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_tasks": len(rows),
        "clean_label_counts": dict(Counter(row["clean_label"] for row in rows)),
        "overall": {
            "baseline_solved": r092["baseline_solved"],
            "forced_template_solved": r092["forced_template_solved"],
            "gate_solved": r092["gate_solved"],
            "fix_harm": r092["gate_fix_harm"],
        },
        "by_clean_label": {
            label: _bucket_summary(label_rows) for label, label_rows in by_label.items()
        },
        "decision_field_violations": r092["decision_field_violations"],
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    bucket_lines = []
    for label, bucket in summary["by_clean_label"].items():
        bucket_lines.extend(
            [
                f"### {label}",
                "",
                f"- Tasks: `{bucket['num_tasks']}`",
                f"- ARG baseline solved: `{bucket['baseline_solved']}/{bucket['num_tasks']}`",
                f"- Forced-template solved: `{bucket['forced_template_solved']}/{bucket['num_tasks']}`",
                f"- R088-gated solved: `{bucket['gate_solved']}/{bucket['num_tasks']}`",
                f"- Fix/harm vs ARG: `{bucket['fix_harm']}`",
                f"- Fix tasks: `{bucket['fix_tasks']}`",
                f"- Harm tasks: `{bucket['harm_tasks']}`",
                "",
            ]
        )
    interesting = [
        row
        for row in summary["rows"]
        if (not row["baseline_is_solved"] and row["gate_is_solved"])
        or (row["baseline_is_solved"] and not row["gate_is_solved"])
    ]
    table_rows = [
        "| `{task}` | `{label}` | `{base}` | `{forced}` | `{gate}` | `{gold}` | `{issue}` |".format(
            task=row["task_id"],
            label=row["clean_label"],
            base=row["baseline_prediction"],
            forced=row["forced_template_prediction"],
            gate=row["gate_prediction"],
            gold=row["true_answer"],
            issue=row["rationale_issue"],
        )
        for row in interesting
    ]
    return "\n".join(
        [
            "# R093 R092 Forced-Template Clean/Noisy Audit Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['num_tasks']}`",
            f"- Clean-label counts: `{summary['clean_label_counts']}`",
            f"- Overall: `{summary['overall']}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            "",
            "## Buckets",
            "",
            *bucket_lines,
            "## Fix/Harm Rows",
            "",
            "| Task | Audit label | ARG | Forced template | Gate | Gold | Rationale issue |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R092's only official fix is on a noisy row (`task_108`), while both official harms "
            "(`task_8`, `task_188`) are clean rows. This makes rank-1 forced templates plus the "
            "current exact-contract gate unsuitable as a main SCI-Q2 result. Future selectors must "
            "separate clean harms from noisy-label fixes before another full API run.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit R092 forced-template full tail34 results by clean/noisy labels.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_tail34_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    clean = summary["by_clean_label"]["clean"]
    noisy = summary["by_clean_label"]["noisy"]
    print(
        "Built R093 clean/noisy audit: "
        f"clean_gate={clean['gate_solved']}/{clean['num_tasks']} "
        f"noisy_gate={noisy['gate_solved']}/{noisy['num_tasks']}"
    )


if __name__ == "__main__":
    main()
