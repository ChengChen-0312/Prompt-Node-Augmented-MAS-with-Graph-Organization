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

from experiment.aqua.forced_template_gate_r058_stress import (  # noqa: E402
    DEFAULT_BASELINE_RESULTS,
    DEFAULT_R058_RESULTS,
    _load_jsonl_by_task,
    _repo_path,
)
from experiment.aqua.forced_template_smoke_gate import (  # noqa: E402
    FORBIDDEN_DECISION_FIELDS,
    extract_option_text,
    is_none_of_these_text,
    normalize_option,
)
from experiment.aqua.forced_template_smoke_report import (  # noqa: E402
    _has_promptnode_graph,
    write_json,
    write_text,
)
from experiment.aqua.offline_utility_selector import (  # noqa: E402
    extract_contract_consensus_features,
)


RULE_NAME = "r088_bad_exact_contract_gate"
CLAIM_BOUNDARY = "r058 replay gate candidate, not fresh accuracy"

DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r088_bad_exact_contract_gate_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r088_bad_exact_contract_gate_report.md"


def build_bad_exact_features(record: Dict[str, Any]) -> Dict[str, Any]:
    contract_features = extract_contract_consensus_features(record)
    predicted_answer = normalize_option(record.get("predicted_answer"))
    option_text = extract_option_text(record.get("question") or "", predicted_answer)
    return {
        "router_option": normalize_option(contract_features.get("router_option")),
        "router_binding_status": str(
            contract_features.get("router_binding_status") or ""
        ).upper(),
        "predicted_answer": predicted_answer,
        "predicted_option_text": option_text,
        "predicted_option_is_none_of_these": is_none_of_these_text(option_text),
        "has_promptnode_graph": _has_promptnode_graph(record),
        "strong_router_contract_count": int(
            contract_features.get("strong_router_contract_count") or 0
        ),
        "direct_majority": normalize_option(contract_features.get("direct_majority")),
        "direct_majority_count": int(contract_features.get("direct_majority_count") or 0),
        "direct_valid_vote_count": int(contract_features.get("direct_valid_vote_count") or 0),
        "router_matches_direct_majority": bool(
            contract_features.get("router_matches_direct_majority")
        ),
        "router_conflicts_with_direct_majority": bool(
            contract_features.get("router_conflicts_with_direct_majority")
        ),
        "all_router_contracts_weak": bool(contract_features.get("all_router_contracts_weak")),
    }


def decide_bad_exact_gate(features: Dict[str, Any]) -> Dict[str, str]:
    if not features.get("has_promptnode_graph"):
        return {"action": "fallback_to_arg", "reason": "missing_promptnode_graph"}

    router_option = normalize_option(features.get("router_option"))
    router_status = str(features.get("router_binding_status") or "").upper()
    predicted = normalize_option(features.get("predicted_answer"))

    if router_status == "EXACT_MATCH" and router_option and predicted == router_option:
        if features.get("router_conflicts_with_direct_majority"):
            return {"action": "fallback_to_arg", "reason": "exact_conflicts_direct_majority"}
        direct_valid = int(features.get("direct_valid_vote_count") or 0)
        direct_majority = int(features.get("direct_majority_count") or 0)
        if direct_valid > direct_majority and direct_majority < 2:
            return {"action": "fallback_to_arg", "reason": "exact_single_vote_split"}
        return {"action": "accept_template", "reason": "trusted_exact_contract"}

    if router_status == "NO_EXACT_OPTION" and predicted:
        if features.get("predicted_option_is_none_of_these"):
            return {"action": "fallback_to_arg", "reason": "weak_none_of_these_boundary"}
        return {
            "action": "fallback_to_arg",
            "reason": "weak_non_none_requires_more_evidence",
        }

    return {"action": "fallback_to_arg", "reason": "unsupported_router_status"}


def build_bad_exact_gate_rows(
    baseline_results: str = DEFAULT_BASELINE_RESULTS,
    r058_results: str = DEFAULT_R058_RESULTS,
) -> List[Dict[str, Any]]:
    baseline = _load_jsonl_by_task(baseline_results)
    r058 = _load_jsonl_by_task(r058_results)
    rows = []
    for task_id in sorted(r058):
        prompt_record = r058[task_id]
        base_record = baseline[task_id]
        features = build_bad_exact_features(prompt_record)
        decision = decide_bad_exact_gate(features)
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


def build_bad_exact_gate_summary() -> Dict[str, Any]:
    rows = build_bad_exact_gate_rows()
    accepted_switch_tasks = [
        row["task_id"]
        for row in rows
        if row["gate_action"] == "accept_template"
        and row["baseline_prediction"] != row["promptnode_prediction"]
    ]
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
        "accepted_switch_tasks": accepted_switch_tasks,
        "fallback_harm_prevented_tasks": [
            row["task_id"]
            for row in rows
            if row["baseline_is_solved"]
            and not row["dense_promptnode_is_solved"]
            and row["gate_is_solved"]
        ],
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    important_rows = [
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
        if row["baseline_prediction"] != row["promptnode_prediction"]
        or row["gate_reason"] in {"exact_conflicts_direct_majority", "exact_single_vote_split"}
    ]
    return "\n".join(
        [
            "# R088 Bad-Exact-Contract Gate Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['num_tasks']}`",
            f"- ARG baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- Dense R058 PromptNode solved: `{summary['dense_promptnode_solved']}/{summary['num_tasks']}`",
            f"- Bad-exact gate solved: `{summary['gate_solved']}/{summary['num_tasks']}`",
            f"- Gate fix/harm vs ARG: `{summary['gate_fix_harm']}`",
            f"- Accepted switch tasks: `{summary['accepted_switch_tasks']}`",
            f"- Fallback harm-prevented tasks: `{summary['fallback_harm_prevented_tasks']}`",
            f"- Gate reasons: `{summary['gate_reason_counts']}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            "",
            "| Task | ARG | R058 PN | Gate | Gold | Gate action | Gate reason |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *important_rows,
            "",
            "## Interpretation",
            "",
            "R088 fixes the failure mode exposed by R087. It does not trust `EXACT_MATCH` by itself: exact contracts are "
            "suppressed when they conflict with a direct-agent majority or when multiple direct agents split and the "
            "router only follows a single vote. On dense R058 traces this preserves the useful `task_108` switch and "
            "falls back on the three harmful R058 switches. This is still a replay-derived gate candidate, not a fresh "
            "forced-template accuracy result.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay a bad-exact-contract gate on R058 tail34 traces.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_bad_exact_gate_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built bad-exact-contract gate report: "
        f"baseline={summary['baseline_solved']}/{summary['num_tasks']} "
        f"r058={summary['dense_promptnode_solved']}/{summary['num_tasks']} "
        f"gate={summary['gate_solved']}/{summary['num_tasks']}"
    )


if __name__ == "__main__":
    main()
