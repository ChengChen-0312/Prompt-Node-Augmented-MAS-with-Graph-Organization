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

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.objective_safety_template_plan import (  # noqa: E402
    FORBIDDEN_SELECTOR_INPUT_FIELDS,
)


RULE_NAME = "r124_explicit_template_guarded_smoke"
CLAIM_BOUNDARY = (
    "same-four-task explicit-template guarded smoke; broader claims require the smoke gate to pass"
)

REGRESSION_TASKS = ["task_8", "task_108", "task_188", "task_250"]
SWITCH_TASK_INDICES = [108, 250]

DEFAULT_BASELINE_JSONL = "experiment/aqua/aqua_tail34_arg_baseline_results.jsonl"
DEFAULT_FORCED_JSONL = (
    "experiment/aqua/aqua_tail34_r124_explicit_template_guarded_switch_results.jsonl"
)
DEFAULT_FORCED_SUMMARY_JSONL = (
    "experiment/aqua/res_logs/aqua_tail34_r124_explicit_template_guarded_switch_summary.jsonl"
)
DEFAULT_R097_PLAN_JSONL = "experiment/aqua/aqua_tail34_r097_objective_safety_template_plan.jsonl"
DEFAULT_AUDIT_FILE = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_TASK_SPLIT = (
    "experiment/aqua/task_split_aqua_tail34_r124_explicit_template_guarded_switches.json"
)
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r124_explicit_template_guarded_smoke.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r124_explicit_template_guarded_smoke_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r124_explicit_template_guarded_smoke_report.md"
)


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _index_by_task(path: str) -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_jsonl(path)}


def _normalize_option(value: Any) -> str:
    match = re.search(r"[A-E]", str(value or "").upper())
    return match.group(0) if match else ""


def _ratio(count: int, total: int) -> str:
    return f"{int(count)}/{int(total)}"


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_switch_task_split(path: str = DEFAULT_TASK_SPLIT) -> Dict[str, Any]:
    payload = {"test_indices": list(SWITCH_TASK_INDICES)}
    write_json(_repo_path(path), payload)
    return payload


def build_evaluate_command(
    task_split_path: str = DEFAULT_TASK_SPLIT,
    output_file: str = DEFAULT_FORCED_JSONL,
    summary_log_file: str = DEFAULT_FORCED_SUMMARY_JSONL,
) -> str:
    return (
        ".venv/bin/python experiment/aqua/evaluate_aqua.py "
        "--dataset_path datasets/AQuA/AQuA.jsonl "
        f"--task_split_path {task_split_path} "
        "--llm_name gpt-4o-2024-08-06 "
        "--decision_method RouterContractFinalRefer "
        f"--output_file {output_file} "
        f"--summary_log_file {summary_log_file} "
        "--eval_batch_size 1 "
        "--forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl "
        "--forced_template_candidate_rank 1"
    )


def _load_audit_labels(path: str) -> Dict[str, str]:
    labels = {}
    if not os.path.exists(_repo_path(path)):
        return labels
    for row in _load_jsonl(path):
        task_id = row.get("task_id")
        if not task_id:
            continue
        labels[task_id] = (
            row.get("audit_label")
            or row.get("clean_label")
            or row.get("label")
            or row.get("gold_binding_status")
            or ""
        )
    return labels


def _selected_rank(record: Dict[str, Any]) -> int:
    index = int(record.get("selected_candidate_index") or 0)
    candidates = record.get("candidate_graphs") or []
    if index < len(candidates):
        return int(candidates[index].get("rank") or index + 1)
    return index + 1


def _has_promptnode_graph(record: Dict[str, Any]) -> bool:
    roles = (record.get("generated_graph") or {}).get("roles") or []
    return any(str(role).startswith("PN_") for role in roles)


def _candidate_has_update2_metadata(template: Dict[str, Any]) -> bool:
    roles = set(template.get("prompt_node_roles") or [])
    specs = template.get("prompt_node_specs") or []
    if not {"PN_Memory", "PN_Verifier", "PN_Router"}.issubset(roles):
        return False
    if not (template.get("graph") or {}).get("edge_permissions"):
        return False
    for spec in specs:
        if not spec.get("identity_type"):
            return False
        if not spec.get("permissions"):
            return False
        if not spec.get("budget"):
            return False
        if not spec.get("lifecycle_actions"):
            return False
        if not spec.get("content_schema"):
            return False
        if not spec.get("insertion_pattern"):
            return False
    return True


def _selector_input_violation_count(plan_rows: Sequence[Dict[str, Any]]) -> int:
    count = 0
    forbidden = set(FORBIDDEN_SELECTOR_INPUT_FIELDS)
    for row in plan_rows:
        selector_input = row.get("selector_input") or {}
        count += sum(1 for key in selector_input if key in forbidden)
    return count


def _is_solved(prediction: Any, truth: Any) -> bool:
    return _normalize_option(prediction) == _normalize_option(truth)


def build_explicit_template_guarded_smoke_rows(
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    forced_jsonl: str = DEFAULT_FORCED_JSONL,
    r097_plan_jsonl: str = DEFAULT_R097_PLAN_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
) -> List[Dict[str, Any]]:
    baseline = _index_by_task(baseline_jsonl)
    forced = _index_by_task(forced_jsonl)
    plan = _index_by_task(r097_plan_jsonl)
    audit_labels = _load_audit_labels(audit_file)
    rows = []
    for task_id in REGRESSION_TASKS:
        plan_row = plan[task_id]
        base = baseline[task_id]
        requires_api = bool(plan_row.get("requires_api_execution"))
        forced_row = forced.get(task_id) if requires_api else None
        selected_template = plan_row.get("selected_template") or {}
        selected_prediction = (
            forced_row.get("predicted_answer")
            if forced_row
            else base.get("predicted_answer")
        )
        selected_source = (
            "explicit_template_rank1"
            if forced_row
            else "baseline"
            if not requires_api
            else "missing_forced_execution"
        )
        truth = base.get("true_answer") or (forced_row or {}).get("true_answer")
        baseline_solved = _is_solved(base.get("predicted_answer"), truth)
        selected_solved = _is_solved(selected_prediction, truth)
        selected_template_rank = None
        if selected_template:
            selected_template_rank = selected_template.get("rank") or _selected_rank(forced_row or {})
        rows.append(
            {
                "task_id": task_id,
                "clean_label": audit_labels.get(task_id, ""),
                "baseline_prediction": base.get("predicted_answer"),
                "selected_prediction": selected_prediction,
                "forced_template_prediction": (forced_row or {}).get("predicted_answer"),
                "true_answer": truth,
                "selected_source": selected_source,
                "requires_api_execution": requires_api,
                "selected_template_rank": selected_template_rank,
                "baseline_is_solved": baseline_solved,
                "selected_is_solved": selected_solved,
                "fix": (not baseline_solved) and selected_solved,
                "harm": baseline_solved and not selected_solved,
                "has_promptnode_graph": _has_promptnode_graph(forced_row or {})
                if forced_row
                else False,
                "has_update2_metadata": _candidate_has_update2_metadata(selected_template)
                if selected_template
                else False,
                "prompt_node_roles": sorted(selected_template.get("prompt_node_roles") or []),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def _fix_harm(rows: Sequence[Dict[str, Any]]) -> str:
    return _ratio(sum(1 for row in rows if row["fix"]), sum(1 for row in rows if row["harm"]))


def _last_summary_record(path: str) -> Dict[str, Any]:
    if not os.path.exists(_repo_path(path)):
        return {}
    records = _load_jsonl(path)
    return records[-1] if records else {}


def build_explicit_template_guarded_smoke_summary(
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    forced_jsonl: str = DEFAULT_FORCED_JSONL,
    r097_plan_jsonl: str = DEFAULT_R097_PLAN_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
    forced_summary_jsonl: str = DEFAULT_FORCED_SUMMARY_JSONL,
) -> Dict[str, Any]:
    rows = build_explicit_template_guarded_smoke_rows(
        baseline_jsonl=baseline_jsonl,
        forced_jsonl=forced_jsonl,
        r097_plan_jsonl=r097_plan_jsonl,
        audit_file=audit_file,
    )
    plan_rows = [row for row in _load_jsonl(r097_plan_jsonl) if row.get("task_id") in REGRESSION_TASKS]
    switch_rows = [row for row in rows if row["selected_source"] == "explicit_template_rank1"]
    fallback_rows = [row for row in rows if row["selected_source"] == "baseline"]
    clean_rows = [row for row in rows if row.get("clean_label") == "clean"]
    noisy_rows = [row for row in rows if row.get("clean_label") != "clean"]
    total = len(rows)
    promptnode_switches = sum(1 for row in switch_rows if row["has_promptnode_graph"])
    metadata_switches = sum(1 for row in switch_rows if row["has_update2_metadata"])
    selector_input_violations = _selector_input_violation_count(plan_rows)
    clean_harms = sum(1 for row in clean_rows if row["harm"])
    clean_fixes = sum(1 for row in clean_rows if row["fix"])
    forced_summary = _last_summary_record(forced_summary_jsonl)
    smoke_gate_passed = (
        bool(switch_rows)
        and promptnode_switches == len(switch_rows)
        and metadata_switches == len(switch_rows)
        and selector_input_violations == 0
        and clean_harms == 0
        and clean_fixes > 0
        and sum(row["selected_is_solved"] for row in rows)
        >= sum(row["baseline_is_solved"] for row in rows)
    )
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_tasks": total,
        "baseline_accuracy": _ratio(sum(row["baseline_is_solved"] for row in rows), total),
        "selected_accuracy": _ratio(sum(row["selected_is_solved"] for row in rows), total),
        "switch_tasks": [row["task_id"] for row in switch_rows],
        "fallback_tasks": [row["task_id"] for row in fallback_rows],
        "promptnode_graph_evidence_on_switches": _ratio(promptnode_switches, len(switch_rows)),
        "switch_update2_metadata": _ratio(metadata_switches, len(switch_rows)),
        "fix_harm": _fix_harm(rows),
        "clean_fix_harm": _fix_harm(clean_rows),
        "noisy_fix_harm": _fix_harm(noisy_rows),
        "selector_input_field_violations": selector_input_violations,
        "forced_cost": float(forced_summary.get("cost") or 0.0),
        "forced_prompt_tokens": int(forced_summary.get("prompt_tokens") or 0),
        "forced_completion_tokens": int(forced_summary.get("completion_tokens") or 0),
        "smoke_gate_passed": smoke_gate_passed,
        "broad_api_allowed_next": smoke_gate_passed,
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{label}` | `{source}` | `{base}` | `{sel}` | `{truth}` | `{fix}` | `{harm}` | `{pn}` | `{meta}` |".format(
            task=row["task_id"],
            label=row.get("clean_label", ""),
            source=row["selected_source"],
            base=row["baseline_prediction"],
            sel=row["selected_prediction"],
            truth=row["true_answer"],
            fix=row["fix"],
            harm=row["harm"],
            pn=row["has_promptnode_graph"],
            meta=row["has_update2_metadata"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R124 Explicit-Template Guarded Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Total tasks: `{summary['total_tasks']}`",
            f"- Baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- Selected accuracy: `{summary['selected_accuracy']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- PromptNode graph evidence on switches: `{summary['promptnode_graph_evidence_on_switches']}`",
            f"- Switch update2 metadata: `{summary['switch_update2_metadata']}`",
            f"- Fix/harm: `{summary['fix_harm']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            f"- Selector input field violations: `{summary['selector_input_field_violations']}`",
            f"- Forced-template cost: `${summary['forced_cost']:.6f}`",
            f"- Smoke gate passed: `{summary['smoke_gate_passed']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            "",
            "| Task | Audit label | Source | ARG | Selected | Truth | Fix | Harm | PN graph | Update2 metadata |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R124 tests only the R123-approved four-task explicit-template guarded policy. "
            "The result can permit a broader run only if switches carry PromptNode graph/update2 metadata, "
            "there are no selector-input violations, no clean harms occur, and at least one clean fix is recovered.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize R124 explicit-template guarded smoke.")
    parser.add_argument("--write-task-split", action="store_true")
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    if args.write_task_split:
        write_switch_task_split(DEFAULT_TASK_SPLIT)
        print(build_evaluate_command())
        return
    summary = build_explicit_template_guarded_smoke_summary()
    write_jsonl(_repo_path(args.output_jsonl), summary["rows"])
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R124 explicit-template guarded smoke report: "
        f"selected={summary['selected_accuracy']} clean_fix_harm={summary['clean_fix_harm']} "
        f"broad_api={summary['broad_api_allowed_next']}"
    )


if __name__ == "__main__":
    main()
