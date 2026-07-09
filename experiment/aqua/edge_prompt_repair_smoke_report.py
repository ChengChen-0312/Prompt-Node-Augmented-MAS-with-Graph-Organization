import argparse
import datetime
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Sequence


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.clean_fix_graph_policy_selector_presmoke import (  # noqa: E402
    FORBIDDEN_SELECTOR_INPUT_FIELDS,
)
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.rank5_high_fanin_selector_smoke_report import (  # noqa: E402
    _candidate_has_update2_metadata,
    _memory_write_count,
)


RULE_NAME = "r137_edge_prompt_repair_smoke"
CLAIM_BOUNDARY = (
    "same-four-task edge-prompt repair smoke; broad claims require clean recovery, "
    "full held-out validation, and transfer"
)
DECISION_METHOD = "EdgePromptRepairContractFinalRefer"

REGRESSION_TASKS = ["task_8", "task_108", "task_188", "task_250"]

DEFAULT_BASELINE_JSONL = "experiment/aqua/aqua_tail34_arg_baseline_results.jsonl"
DEFAULT_FORCED_JSONL = "experiment/aqua/aqua_tail34_r137_edge_prompt_repair_switch_results.jsonl"
DEFAULT_FORCED_SUMMARY_JSONL = (
    "experiment/aqua/res_logs/aqua_tail34_r137_edge_prompt_repair_switch_summary.jsonl"
)
DEFAULT_R127_PLAN_JSONL = "experiment/aqua/aqua_tail34_r127_clean_fix_graph_policy_selector_presmoke.jsonl"
DEFAULT_AUDIT_FILE = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r137_edge_prompt_repair_smoke.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r137_edge_prompt_repair_smoke_summary.json"
)
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r137_edge_prompt_repair_smoke_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _index_by_task(path: str) -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_jsonl(path)}


def _normalize_option(value: Any) -> str:
    value = str(value or "").strip()
    if value in {"A", "B", "C", "D", "E"}:
        return value
    match = re.search(r"\b([A-E])\b", value.upper())
    return match.group(1) if match else value


def _is_solved(prediction: Any, truth: Any) -> bool:
    return _normalize_option(prediction) == _normalize_option(truth)


def _ratio(count: int, total: int) -> str:
    return f"{int(count)}/{int(total)}"


def _load_audit_labels(path: str) -> Dict[str, str]:
    labels: Dict[str, str] = {}
    if not os.path.exists(_repo_path(path)):
        return labels
    for row in _load_jsonl(path):
        task_id = row.get("task_id")
        if task_id:
            labels[task_id] = (
                row.get("audit_label")
                or row.get("clean_label")
                or row.get("label")
                or row.get("gold_binding_status")
                or ""
            )
    return labels


def _agent_output(record: Dict[str, Any], role: str) -> str:
    for output in record.get("agent_outputs") or []:
        if output.get("role") == role:
            return "\n".join(str(item) for item in output.get("outputs") or [])
    return ""


def _extract_contract_field(text: str, field: str) -> str:
    match = re.search(rf"^{field}:\s*(.+)$", text or "", flags=re.I | re.M)
    return re.sub(r"\s+", " ", match.group(1)).strip().upper() if match else ""


def _has_promptnode_graph(record: Dict[str, Any]) -> bool:
    roles = (record.get("generated_graph") or {}).get("roles") or []
    return any(str(role).startswith("PN_") for role in roles)


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_SELECTOR_INPUT_FIELDS or _contains_forbidden_key(child):
                return True
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _selector_input_violation_count(plan_rows: Sequence[Dict[str, Any]]) -> int:
    return sum(1 for row in plan_rows if _contains_forbidden_key(row.get("selector_input") or {}))


def _fix_harm(rows: Sequence[Dict[str, Any]]) -> str:
    return _ratio(sum(1 for row in rows if row["fix"]), sum(1 for row in rows if row["harm"]))


def _last_summary_record(path: str) -> Dict[str, Any]:
    if not os.path.exists(_repo_path(path)):
        return {}
    records = _load_jsonl(path)
    return records[-1] if records else {}


def _router_repair_fields_present(router_text: str) -> bool:
    return all(
        _extract_contract_field(router_text, field)
        for field in [
            "REPAIR_OPTION",
            "REPAIR_BINDING_STATUS",
            "REPAIR_CONFIDENCE",
            "REPAIR_DISTANCE_RATIO",
        ]
    )


def _verifier_repair_candidate_present(verifier_text: str) -> bool:
    return "REPAIR_CANDIDATE_AUDIT" in verifier_text and bool(re.search(
        r"Repair\s+Option\W+\s*[A-E]", verifier_text, flags=re.I
    ))


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_edge_prompt_repair_smoke_rows(
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    forced_jsonl: str = DEFAULT_FORCED_JSONL,
    r127_plan_jsonl: str = DEFAULT_R127_PLAN_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
) -> List[Dict[str, Any]]:
    baseline = _index_by_task(baseline_jsonl)
    forced = _index_by_task(forced_jsonl)
    plan = _index_by_task(r127_plan_jsonl)
    audit_labels = _load_audit_labels(audit_file)

    rows: List[Dict[str, Any]] = []
    for task_id in REGRESSION_TASKS:
        plan_row = plan[task_id]
        base = baseline[task_id]
        should_switch = plan_row.get("planned_action") == "switch_to_promptnode_template"
        forced_row = forced.get(task_id) if should_switch else None
        selected_template = plan_row.get("selected_template") or {}
        selected_prediction = forced_row.get("predicted_answer") if forced_row else base.get("predicted_answer")
        truth = base.get("true_answer") or (forced_row or {}).get("true_answer")
        baseline_solved = _is_solved(base.get("predicted_answer"), truth)
        selected_solved = _is_solved(selected_prediction, truth)
        router_text = _agent_output(forced_row or {}, "PN_Router")
        verifier_text = _agent_output(forced_row or {}, "PN_Verifier")
        repair_option = _extract_contract_field(router_text, "REPAIR_OPTION")
        rows.append(
            {
                "task_id": task_id,
                "clean_label": audit_labels.get(task_id, ""),
                "baseline_prediction": base.get("predicted_answer"),
                "selected_prediction": selected_prediction,
                "true_answer": truth,
                "selected_source": f"rank5_{DECISION_METHOD}" if forced_row else "baseline",
                "selected_template_rank": selected_template.get("rank") if selected_template else None,
                "baseline_is_solved": baseline_solved,
                "selected_is_solved": selected_solved,
                "fix": (not baseline_solved) and selected_solved,
                "harm": baseline_solved and not selected_solved,
                "has_promptnode_graph": _has_promptnode_graph(forced_row or {}) if forced_row else False,
                "has_update2_metadata": _candidate_has_update2_metadata(selected_template),
                "has_high_fanin_memory_bridge": (
                    _memory_write_count(selected_template) >= 3 if selected_template else False
                ),
                "router_supported_option": _extract_contract_field(router_text, "SUPPORTED_OPTION"),
                "router_binding_status": _extract_contract_field(router_text, "BINDING_STATUS"),
                "router_repair_option": repair_option,
                "router_repair_binding_status": _extract_contract_field(router_text, "REPAIR_BINDING_STATUS"),
                "router_repair_confidence": _extract_contract_field(router_text, "REPAIR_CONFIDENCE"),
                "router_repair_distance_ratio": _extract_contract_field(router_text, "REPAIR_DISTANCE_RATIO"),
                "router_repair_fields_present": _router_repair_fields_present(router_text),
                "router_repair_option_non_none": repair_option not in {"", "NONE"},
                "verifier_repair_candidate_present": _verifier_repair_candidate_present(verifier_text),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_edge_prompt_repair_smoke_summary(
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    forced_jsonl: str = DEFAULT_FORCED_JSONL,
    r127_plan_jsonl: str = DEFAULT_R127_PLAN_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
    forced_summary_jsonl: str = DEFAULT_FORCED_SUMMARY_JSONL,
) -> Dict[str, Any]:
    rows = build_edge_prompt_repair_smoke_rows(
        baseline_jsonl=baseline_jsonl,
        forced_jsonl=forced_jsonl,
        r127_plan_jsonl=r127_plan_jsonl,
        audit_file=audit_file,
    )
    plan_rows = [row for row in _load_jsonl(r127_plan_jsonl) if row.get("task_id") in REGRESSION_TASKS]
    switch_rows = [row for row in rows if row["selected_source"] != "baseline"]
    fallback_rows = [row for row in rows if row["selected_source"] == "baseline"]
    clean_rows = [row for row in rows if row.get("clean_label") == "clean"]
    noisy_rows = [row for row in rows if row.get("clean_label") != "clean"]
    task250 = next(row for row in rows if row["task_id"] == "task_250")
    forced_summary = _last_summary_record(forced_summary_jsonl)
    integrity_gate_passed = (
        sum(1 for row in switch_rows if row["has_promptnode_graph"]) == len(switch_rows)
        and sum(1 for row in switch_rows if row["has_update2_metadata"]) == len(switch_rows)
        and sum(1 for row in switch_rows if row["router_repair_fields_present"]) == len(switch_rows)
        and _selector_input_violation_count(plan_rows) == 0
    )
    smoke_gate_passed = (
        integrity_gate_passed
        and sum(row["harm"] for row in clean_rows) == 0
        and sum(row["fix"] for row in clean_rows) > 0
        and sum(row["selected_is_solved"] for row in rows)
        >= sum(row["baseline_is_solved"] for row in rows)
    )
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "decision_method": DECISION_METHOD,
        "total_tasks": len(rows),
        "baseline_accuracy": _ratio(sum(row["baseline_is_solved"] for row in rows), len(rows)),
        "selected_accuracy": _ratio(sum(row["selected_is_solved"] for row in rows), len(rows)),
        "switch_tasks": [row["task_id"] for row in switch_rows],
        "fallback_tasks": [row["task_id"] for row in fallback_rows],
        "promptnode_graph_evidence_on_switches": _ratio(
            sum(1 for row in switch_rows if row["has_promptnode_graph"]), len(switch_rows)
        ),
        "switch_update2_metadata": _ratio(
            sum(1 for row in switch_rows if row["has_update2_metadata"]), len(switch_rows)
        ),
        "high_fanin_memory_bridge_on_switches": _ratio(
            sum(1 for row in switch_rows if row["has_high_fanin_memory_bridge"]), len(switch_rows)
        ),
        "fix_harm": _fix_harm(rows),
        "clean_fix_harm": _fix_harm(clean_rows),
        "noisy_fix_harm": _fix_harm(noisy_rows),
        "switch_router_repair_fields_present": _ratio(
            sum(1 for row in switch_rows if row["router_repair_fields_present"]), len(switch_rows)
        ),
        "switch_router_repair_option_non_none": _ratio(
            sum(1 for row in switch_rows if row["router_repair_option_non_none"]), len(switch_rows)
        ),
        "task250_verifier_repair_candidate_present": task250["verifier_repair_candidate_present"],
        "task250_router_repair_forwarded": task250["router_repair_option_non_none"],
        "verifier_router_repair_forwarding_gap": (
            task250["verifier_repair_candidate_present"]
            and not task250["router_repair_option_non_none"]
        ),
        "selector_input_field_violations": _selector_input_violation_count(plan_rows),
        "forced_cost": float(forced_summary.get("cost") or 0.0),
        "forced_prompt_tokens": int(forced_summary.get("prompt_tokens") or 0),
        "forced_completion_tokens": int(forced_summary.get("completion_tokens") or 0),
        "integrity_gate_passed": integrity_gate_passed,
        "smoke_gate_passed": smoke_gate_passed,
        "broad_api_allowed_next": False,
        "next_protocol": "router_repair_field_forwarding_prompt_hardening",
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{label}` | `{source}` | `{base}` | `{sel}` | `{truth}` | `{repair}` | `{verifier}` | `{fix}` | `{harm}` |".format(
            task=row["task_id"],
            label=row.get("clean_label", ""),
            source=row["selected_source"],
            base=row["baseline_prediction"],
            sel=row["selected_prediction"],
            truth=row["true_answer"],
            repair=row["router_repair_option"],
            verifier=row["verifier_repair_candidate_present"],
            fix=row["fix"],
            harm=row["harm"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R137 Edge-Prompt Repair Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Decision method: `{summary['decision_method']}`",
            f"- Baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- Selected accuracy: `{summary['selected_accuracy']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- PN graph evidence on switches: `{summary['promptnode_graph_evidence_on_switches']}`",
            f"- Switch update2 metadata: `{summary['switch_update2_metadata']}`",
            f"- Fix/harm: `{summary['fix_harm']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            f"- Switch router repair fields present: `{summary['switch_router_repair_fields_present']}`",
            f"- Switch router repair option non-none: `{summary['switch_router_repair_option_non_none']}`",
            f"- task250 verifier repair candidate present: `{summary['task250_verifier_repair_candidate_present']}`",
            f"- task250 router repair forwarded: `{summary['task250_router_repair_forwarded']}`",
            f"- Verifier-router repair forwarding gap: `{summary['verifier_router_repair_forwarding_gap']}`",
            f"- Forced cost: `${summary['forced_cost']:.6f}`",
            f"- Integrity gate passed: `{summary['integrity_gate_passed']}`",
            f"- Smoke gate passed: `{summary['smoke_gate_passed']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "| Task | Label | Source | Baseline | Selected | Truth | Router repair | Verifier repair candidate | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R137 confirms the repair fields are emitted in PN_Router output, so the edge-prompt interface "
            "is live. However, task250 still fails because PN_Verifier suggests a repair candidate while "
            "PN_Router forwards `REPAIR_OPTION: NONE`. The next correction is therefore the verifier-to-router "
            "repair forwarding prompt, not broader evaluation.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize R137 edge-prompt repair smoke.")
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_edge_prompt_repair_smoke_rows()
    summary = build_edge_prompt_repair_smoke_summary()
    write_jsonl(args.output_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R137 edge-prompt repair smoke report: "
        f"selected={summary['selected_accuracy']} integrity={summary['integrity_gate_passed']} "
        f"smoke={summary['smoke_gate_passed']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
