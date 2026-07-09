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

from experiment.aqua.forced_template_smoke_gate import (  # noqa: E402
    FORBIDDEN_DECISION_FIELDS,
    build_decision_features,
    decide_forced_template_gate,
)
from experiment.aqua.forced_template_smoke_report import (  # noqa: E402
    _extract_contract_field,
    _has_promptnode_graph,
    _load_first_jsonl,
    _router_output,
    write_json,
    write_text,
)


RULE_NAME = "r087_r086_gate_on_r058_stress"
CLAIM_BOUNDARY = "r058 stress replay, not a new accuracy method"

DEFAULT_BASELINE_RESULTS = "experiment/aqua/aqua_tail34_arg_baseline_results.jsonl"
DEFAULT_R058_RESULTS = "experiment/aqua/aqua_tail34_r058_router_contract_terminal_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r087_r086_gate_on_r058_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r087_r086_gate_on_r058_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_jsonl_by_task(path: str) -> Dict[str, Dict[str, Any]]:
    records = {}
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                records[record["task_id"]] = record
    return records


def _r058_decision_row(record: Dict[str, Any]) -> Dict[str, Any]:
    router_text = _router_output(record)
    return {
        "question": record.get("question") or "",
        "predicted_answer": record.get("predicted_answer"),
        "router_supported_option": _extract_contract_field(router_text, "SUPPORTED_OPTION"),
        "router_binding_status": _extract_contract_field(router_text, "BINDING_STATUS"),
        "selected_rank": 1,
        "has_promptnode_graph": _has_promptnode_graph(record),
        "num_nodes": record.get("num_nodes"),
        "num_edges": record.get("num_edges"),
    }


def build_r058_stress_rows(
    baseline_results: str = DEFAULT_BASELINE_RESULTS,
    r058_results: str = DEFAULT_R058_RESULTS,
) -> List[Dict[str, Any]]:
    baseline = _load_jsonl_by_task(baseline_results)
    r058 = _load_jsonl_by_task(r058_results)
    rows = []
    for task_id in sorted(r058):
        prompt_record = r058[task_id]
        base_record = baseline[task_id]
        decision_row = _r058_decision_row(prompt_record)
        features = build_decision_features(decision_row)
        decision = decide_forced_template_gate(features)
        final_record = prompt_record if decision["action"] == "accept_template" else base_record
        rows.append(
            {
                "task_id": task_id,
                "baseline_prediction": base_record.get("predicted_answer"),
                "promptnode_prediction": prompt_record.get("predicted_answer"),
                "gate_prediction": final_record.get("predicted_answer"),
                "true_answer": prompt_record.get("true_answer"),
                "baseline_is_solved": bool(base_record.get("is_solved")),
                "dense_promptnode_is_solved": bool(prompt_record.get("is_solved")),
                "gate_is_solved": bool(final_record.get("is_solved")),
                "router_supported_option": decision_row["router_supported_option"],
                "router_binding_status": decision_row["router_binding_status"],
                "gate_action": decision["action"],
                "gate_reason": decision["reason"],
                "decision_features": features,
                "decision_field_violation_count": len(
                    FORBIDDEN_DECISION_FIELDS.intersection(features)
                ),
            }
        )
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


def build_r058_stress_summary() -> Dict[str, Any]:
    rows = build_r058_stress_rows()
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_tasks": len(rows),
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "dense_promptnode_solved": sum(
            1 for row in rows if row["dense_promptnode_is_solved"]
        ),
        "gate_solved": sum(1 for row in rows if row["gate_is_solved"]),
        "gate_fix_harm": _fix_harm(rows),
        "gate_action_counts": dict(Counter(row["gate_action"] for row in rows)),
        "gate_reason_counts": dict(Counter(row["gate_reason"] for row in rows)),
        "decision_field_violations": sum(
            row["decision_field_violation_count"] for row in rows
        ),
        "harm_tasks": [
            row["task_id"]
            for row in rows
            if row["baseline_is_solved"] and not row["gate_is_solved"]
        ],
        "fix_tasks": [
            row["task_id"]
            for row in rows
            if not row["baseline_is_solved"] and row["gate_is_solved"]
        ],
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "| `{task}` | `{base}` | `{pn}` | `{gate}` | `{gold}` | `{action}` | `{reason}` |".format(
            task=row["task_id"],
            base=row["baseline_prediction"],
            pn=row["promptnode_prediction"],
            gate=row["gate_prediction"],
            gold=row["true_answer"],
            action=row["gate_action"],
            reason=row["gate_reason"],
        )
        for row in summary["rows"]
        if (
            row["baseline_is_solved"] != row["gate_is_solved"]
            or row["gate_action"] == "fallback_to_arg"
        )
    ]
    return "\n".join(
        [
            "# R087 R086 Gate on R058 Stress Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['num_tasks']}`",
            f"- ARG baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- Dense R058 PromptNode solved: `{summary['dense_promptnode_solved']}/{summary['num_tasks']}`",
            f"- R086-gated replay solved: `{summary['gate_solved']}/{summary['num_tasks']}`",
            f"- Gate fix/harm vs ARG: `{summary['gate_fix_harm']}`",
            f"- Gate actions: `{summary['gate_action_counts']}`",
            f"- Gate reasons: `{summary['gate_reason_counts']}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            "",
            "| Task | ARG | R058 PN | Gate | Gold | Gate action | Gate reason |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## Interpretation",
            "",
            "The R086 smoke gate does not generalize to the dense R058 PromptNode candidate pool. It improves over dense "
            "R058 (`26/34` vs `25/34`) but remains below the ARG baseline (`28/34`) and introduces three harms. "
            "This rejects promoting the current gate to an online full-tail34 method. The next gate must distinguish "
            "bad exact-router contracts from reliable exact contracts, not only suppress weak `None of these` cases.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stress-test the R086 smoke gate on R058 tail34 traces.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_r058_stress_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R086-on-R058 stress report: "
        f"baseline={summary['baseline_solved']}/{summary['num_tasks']} "
        f"r058={summary['dense_promptnode_solved']}/{summary['num_tasks']} "
        f"gate={summary['gate_solved']}/{summary['num_tasks']}"
    )


if __name__ == "__main__":
    main()
