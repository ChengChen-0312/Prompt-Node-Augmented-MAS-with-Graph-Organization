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
from experiment.aqua.clean_fix_graph_policy_selector_presmoke import (  # noqa: E402
    FORBIDDEN_SELECTOR_INPUT_FIELDS,
)


RULE_NAME = "r128_rank5_high_fanin_selector_smoke"
CLAIM_BOUNDARY = (
    "same-four-task rank5 high-fanin selector smoke; broad claims require a fresh R128 API run and separate audit"
)

REGRESSION_TASKS = ["task_8", "task_108", "task_188", "task_250"]
SWITCH_TASK_INDICES = [108, 250]

DEFAULT_BASELINE_JSONL = "experiment/aqua/aqua_tail34_arg_baseline_results.jsonl"
DEFAULT_FORCED_JSONL = "experiment/aqua/aqua_tail34_r128_rank5_high_fanin_switch_results.jsonl"
DEFAULT_FORCED_SUMMARY_JSONL = (
    "experiment/aqua/res_logs/aqua_tail34_r128_rank5_high_fanin_switch_summary.jsonl"
)
DEFAULT_R127_PLAN_JSONL = "experiment/aqua/aqua_tail34_r127_clean_fix_graph_policy_selector_presmoke.jsonl"
DEFAULT_AUDIT_FILE = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_TASK_SPLIT = "experiment/aqua/task_split_aqua_tail34_r128_rank5_high_fanin_switches.json"
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r128_rank5_high_fanin_selector_smoke.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r128_rank5_high_fanin_selector_smoke_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r128_rank5_high_fanin_selector_smoke_report.md"


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
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
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
        "--forced_template_candidate_rank 5"
    )


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


def _is_solved(prediction: Any, truth: Any) -> bool:
    return _normalize_option(prediction) == _normalize_option(truth)


def _has_promptnode_graph(record: Dict[str, Any]) -> bool:
    roles = (record.get("generated_graph") or {}).get("roles") or []
    return any(str(role).startswith("PN_") for role in roles)


def _memory_write_count(candidate: Dict[str, Any] | None) -> int:
    if not candidate:
        return 0
    graph = candidate.get("graph") or {}
    count = 0
    for edge in graph.get("edge_records") or []:
        if edge.get("target_role") == "PN_Memory" and "write" in (edge.get("permissions") or []):
            count += 1
    return count


def _edge_permission_count(candidate: Dict[str, Any] | None) -> int:
    if not candidate:
        return 0
    return len((candidate.get("graph") or {}).get("edge_permissions") or {})


def _candidate_has_update2_metadata(candidate: Dict[str, Any] | None) -> bool:
    if not candidate:
        return False
    if not {"PN_Memory", "PN_Verifier", "PN_Router"}.issubset(
        set(candidate.get("prompt_node_roles") or [])
    ):
        return False
    specs = candidate.get("prompt_node_specs") or []
    if len(specs) < 3:
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
    return _edge_permission_count(candidate) > 0


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


def _last_summary_record(path: str) -> Dict[str, Any]:
    if not os.path.exists(_repo_path(path)):
        return {}
    records = _load_jsonl(path)
    return records[-1] if records else {}


def _fix_harm(rows: Sequence[Dict[str, Any]]) -> str:
    return _ratio(sum(1 for row in rows if row["fix"]), sum(1 for row in rows if row["harm"]))


def build_rank5_high_fanin_selector_smoke_rows(
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    forced_jsonl: str = DEFAULT_FORCED_JSONL,
    r127_plan_jsonl: str = DEFAULT_R127_PLAN_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
) -> List[Dict[str, Any]]:
    baseline = _index_by_task(baseline_jsonl)
    forced = _index_by_task(forced_jsonl)
    plan = _index_by_task(r127_plan_jsonl)
    audit_labels = _load_audit_labels(audit_file)
    rows = []
    for task_id in REGRESSION_TASKS:
        plan_row = plan[task_id]
        base = baseline[task_id]
        should_switch = plan_row.get("planned_action") == "switch_to_promptnode_template"
        forced_row = forced.get(task_id) if should_switch else None
        selected_template = plan_row.get("selected_template") or {}
        selected_prediction = (
            forced_row.get("predicted_answer") if forced_row else base.get("predicted_answer")
        )
        selected_source = "explicit_template_rank5_high_fanin" if forced_row else "baseline"
        truth = base.get("true_answer") or (forced_row or {}).get("true_answer")
        baseline_solved = _is_solved(base.get("predicted_answer"), truth)
        selected_solved = _is_solved(selected_prediction, truth)
        rows.append(
            {
                "task_id": task_id,
                "clean_label": audit_labels.get(task_id, ""),
                "baseline_prediction": base.get("predicted_answer"),
                "selected_prediction": selected_prediction,
                "forced_template_prediction": (forced_row or {}).get("predicted_answer"),
                "true_answer": truth,
                "selected_source": selected_source,
                "requires_api_execution": should_switch,
                "selected_template_rank": selected_template.get("rank") if selected_template else None,
                "baseline_is_solved": baseline_solved,
                "selected_is_solved": selected_solved,
                "fix": (not baseline_solved) and selected_solved,
                "harm": baseline_solved and not selected_solved,
                "has_promptnode_graph": _has_promptnode_graph(forced_row or {}) if forced_row else False,
                "has_update2_metadata": _candidate_has_update2_metadata(selected_template),
                "has_high_fanin_memory_bridge": _memory_write_count(selected_template) >= 3,
                "prompt_node_roles": sorted(selected_template.get("prompt_node_roles") or []),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_rank5_high_fanin_selector_smoke_summary(
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    forced_jsonl: str = DEFAULT_FORCED_JSONL,
    r127_plan_jsonl: str = DEFAULT_R127_PLAN_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
    forced_summary_jsonl: str = DEFAULT_FORCED_SUMMARY_JSONL,
) -> Dict[str, Any]:
    rows = build_rank5_high_fanin_selector_smoke_rows(
        baseline_jsonl=baseline_jsonl,
        forced_jsonl=forced_jsonl,
        r127_plan_jsonl=r127_plan_jsonl,
        audit_file=audit_file,
    )
    plan_rows = [row for row in _load_jsonl(r127_plan_jsonl) if row.get("task_id") in REGRESSION_TASKS]
    switch_rows = [row for row in rows if row["selected_source"] == "explicit_template_rank5_high_fanin"]
    fallback_rows = [row for row in rows if row["selected_source"] == "baseline"]
    clean_rows = [row for row in rows if row.get("clean_label") == "clean"]
    noisy_rows = [row for row in rows if row.get("clean_label") != "clean"]
    promptnode_switches = sum(1 for row in switch_rows if row["has_promptnode_graph"])
    metadata_switches = sum(1 for row in switch_rows if row["has_update2_metadata"])
    high_fanin_switches = sum(1 for row in switch_rows if row["has_high_fanin_memory_bridge"])
    selector_input_violations = _selector_input_violation_count(plan_rows)
    clean_harms = sum(1 for row in clean_rows if row["harm"])
    clean_fixes = sum(1 for row in clean_rows if row["fix"])
    total = len(rows)
    forced_summary = _last_summary_record(forced_summary_jsonl)
    smoke_gate_passed = (
        bool(switch_rows)
        and promptnode_switches == len(switch_rows)
        and metadata_switches == len(switch_rows)
        and high_fanin_switches == len(switch_rows)
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
        "selected_template_ranks": {
            row["task_id"]: row["selected_template_rank"] for row in switch_rows
        },
        "promptnode_graph_evidence_on_switches": _ratio(promptnode_switches, len(switch_rows)),
        "switch_update2_metadata": _ratio(metadata_switches, len(switch_rows)),
        "high_fanin_memory_bridge_on_switches": _ratio(high_fanin_switches, len(switch_rows)),
        "fix_harm": _fix_harm(rows),
        "clean_fix_harm": _fix_harm(clean_rows),
        "noisy_fix_harm": _fix_harm(noisy_rows),
        "selector_input_field_violations": selector_input_violations,
        "forced_cost": float(forced_summary.get("cost") or 0.0),
        "forced_prompt_tokens": int(float(forced_summary.get("prompt_tokens") or 0)),
        "forced_completion_tokens": int(float(forced_summary.get("completion_tokens") or 0)),
        "smoke_gate_passed": smoke_gate_passed,
        "broad_api_allowed_next": False,
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{label}` | `{source}` | `{rank}` | `{base}` | `{sel}` | `{truth}` | `{fix}` | `{harm}` | `{pn}` | `{fanin}` |".format(
            task=row["task_id"],
            label=row.get("clean_label", ""),
            source=row["selected_source"],
            rank=row["selected_template_rank"],
            base=row["baseline_prediction"],
            sel=row["selected_prediction"],
            truth=row["true_answer"],
            fix=row["fix"],
            harm=row["harm"],
            pn=row["has_promptnode_graph"],
            fanin=row["has_high_fanin_memory_bridge"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R128 Rank5 High-Fanin Selector Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- Selected accuracy: `{summary['selected_accuracy']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- Selected template ranks: `{summary['selected_template_ranks']}`",
            f"- PromptNode graph evidence on switches: `{summary['promptnode_graph_evidence_on_switches']}`",
            f"- Switch update2 metadata: `{summary['switch_update2_metadata']}`",
            f"- High-fanin Memory bridge on switches: `{summary['high_fanin_memory_bridge_on_switches']}`",
            f"- Fix/harm: `{summary['fix_harm']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            f"- Selector input field violations: `{summary['selector_input_field_violations']}`",
            f"- Forced cost: `${summary['forced_cost']:.6f}`",
            f"- Smoke gate passed: `{summary['smoke_gate_passed']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            "",
            "| Task | Label | Source | Rank | Baseline | Selected | Truth | Fix | Harm | PN graph | High fan-in |",
            "| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R128 evaluates the R127 plan only on the same four regression tasks. Passing this smoke would support "
            "a bounded clean-fix mechanism claim, but broad tail34 or transfer evaluation still requires a separate "
            "audit decision.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R128 rank5 high-fanin selector smoke report.")
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_rank5_high_fanin_selector_smoke_rows()
    summary = build_rank5_high_fanin_selector_smoke_summary()
    write_jsonl(args.output_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R128 rank5 high-fanin selector smoke: "
        f"selected={summary['selected_accuracy']} clean={summary['clean_fix_harm']} "
        f"gate={summary['smoke_gate_passed']}"
    )


if __name__ == "__main__":
    main()
