from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Callable, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_jsonl
from experiment.mmlu.r234_tiny_diagnostic_failure_analysis import load_audit_lookup
from experiment.mmlu.r237_apply_conservative_policy import build_source_lookup


def _first(rows: List[Dict[str, Any]], predicate: Callable[[Dict[str, Any]], bool]) -> Dict[str, Any]:
    for row in rows:
        if predicate(row):
            return row
    return {}


def select_case_studies(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {
        "frozen_fix": _first(
            rows,
            lambda row: row.get("split_role") == "frozen_eval" and bool(row.get("fix")),
        ),
        "train_fix": _first(
            rows,
            lambda row: row.get("split_role") == "train" and bool(row.get("fix")),
        ),
        "abstain_protected_clean": _first(
            rows,
            lambda row: (not row.get("switch"))
            and row.get("baseline_correct") is True
            and row.get("selected_correct") is True
            and row.get("clean_label") == "clean",
        ),
        "no_fix_objective_wrong": _first(
            rows,
            lambda row: bool(row.get("switch"))
            and row.get("baseline_correct") is False
            and row.get("selected_correct") is False,
        ),
    }


def enrich_rows(
    records: List[Dict[str, Any]],
    source_paths: List[str],
    audit_paths: List[str],
) -> List[Dict[str, Any]]:
    source_lookup = build_source_lookup(source_paths)
    audit_lookup = load_audit_lookup(audit_paths)
    enriched = []
    for row in records:
        task_id = str(row.get("task_id") or "")
        source = source_lookup.get(task_id, {})
        audit = audit_lookup.get(task_id, {})
        out = dict(row)
        out["question"] = source.get("question", "")
        out["clean_label"] = audit.get("clean_label", "unknown")
        out["gold_binding_status"] = audit.get("gold_binding_status", "unknown")
        out["rationale_issue"] = audit.get("rationale_issue", "unknown")
        out["audit_brief_reason"] = audit.get("brief_reason", "")
        enriched.append(out)
    return enriched


def run_case_study_extraction(
    records_jsonl: str,
    source_paths: List[str],
    audit_paths: List[str],
    output_json: str,
    report_md: str,
) -> Dict[str, Any]:
    records = enrich_rows(load_jsonl(records_jsonl), source_paths, audit_paths)
    selected = select_case_studies(records)
    summary = {
        "run_id": "R244",
        "title": "Conservative policy case studies",
        "claim_boundary": "Case-study extraction only; no API, no superiority claim, and no SCI-Q2 readiness claim.",
        "no_api": True,
        "records_jsonl": records_jsonl,
        "source_paths": source_paths,
        "audit_paths": audit_paths,
        "case_studies": selected,
        "selected_case_ids": {key: value.get("task_id") for key, value in selected.items()},
    }
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def _case_lines(name: str, row: Dict[str, Any]) -> List[str]:
    if not row:
        return [f"### {name}", "", "No matching case found.", ""]
    return [
        f"### {name}",
        "",
        f"- Task: `{row.get('task_id')}` / split `{row.get('split_role')}` / clean `{row.get('clean_label')}`",
        f"- Baseline/objective/selected/true: `{row.get('baseline_prediction')}` / `{row.get('objective_prediction')}` / `{row.get('selected_prediction')}` / `{row.get('true_answer')}`",
        f"- Switch: `{row.get('switch')}`; fix/harm: `{row.get('fix')}` / `{row.get('harm')}`",
        f"- Feature score/majority: `{row.get('objective_top_score')}` / `{row.get('baseline_direct_majority_count')}`",
        f"- Audit: `{row.get('gold_binding_status')}`, `{row.get('rationale_issue')}`",
        f"- Question: {row.get('question')}",
        "",
    ]


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R244 Conservative Policy Case Studies",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"Selected case ids: `{summary['selected_case_ids']}`",
        "",
    ]
    for name, row in summary["case_studies"].items():
        rows.extend(_case_lines(name, row))
    rows.extend(
        [
            "## Interpretation",
            "",
            "These cases support paper discussion but not a result claim. They show where the fitted abstention policy helps, where it protects a clean ARG-correct case, and where neither baseline nor objective evidence is sufficient.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract conservative policy case studies.")
    parser.add_argument("--records_jsonl", required=True)
    parser.add_argument("--source_paths", nargs="+", required=True)
    parser.add_argument("--audit_paths", nargs="*", default=[])
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_case_study_extraction(
        records_jsonl=args.records_jsonl,
        source_paths=args.source_paths,
        audit_paths=args.audit_paths,
        output_json=args.output_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
