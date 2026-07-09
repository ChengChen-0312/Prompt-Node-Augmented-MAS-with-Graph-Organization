import argparse
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r097_objective_safety_template_plan"
CLAIM_BOUNDARY = "explicit template plan from R096/R083; no new API or accuracy result"

FORBIDDEN_SELECTOR_INPUT_FIELDS = {
    "task_id",
    "true_answer",
    "is_solved",
    "baseline_is_solved",
    "objective_selector_is_solved",
    "safety_composed_is_solved",
    "clean_label",
    "audit_label",
    "gold_binding_status",
    "rationale_issue",
    "target_action",
    "target_reason",
    "analysis",
}

DEFAULT_R096_TARGET_JSONL = "experiment/aqua/aqua_tail34_r096_objective_safety_policy_targets.jsonl"
DEFAULT_R083_CANDIDATE_JSONL = "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl"
DEFAULT_PLAN_JSONL = "experiment/aqua/aqua_tail34_r097_objective_safety_template_plan.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r097_objective_safety_template_plan_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r097_objective_safety_template_plan_report.md"


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _candidate_index(candidate_jsonl: str) -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_jsonl(candidate_jsonl)}


def _top_candidate(candidate_row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not candidate_row or not candidate_row.get("candidates"):
        return None
    return candidate_row["candidates"][0]


def _candidate_lifecycle_action_count(candidate: Optional[Dict[str, Any]]) -> int:
    if not candidate:
        return 0
    return sum(len(spec.get("lifecycle_actions", [])) for spec in candidate.get("prompt_node_specs", []))


def _candidate_edge_permission_count(candidate: Optional[Dict[str, Any]]) -> int:
    if not candidate:
        return 0
    graph = candidate.get("graph", {})
    return len(graph.get("edge_permissions", {}))


def _has_update2_metadata(candidate: Optional[Dict[str, Any]]) -> bool:
    if not candidate:
        return False
    required_roles = {"PN_Memory", "PN_Verifier", "PN_Router"}
    roles = set(candidate.get("prompt_node_roles", []))
    specs = candidate.get("prompt_node_specs", [])
    if not required_roles.issubset(roles) or len(specs) < 3:
        return False
    for spec in specs:
        if not spec.get("identity_type"):
            return False
        if not spec.get("insertion_pattern"):
            return False
        if not spec.get("permissions"):
            return False
        if not spec.get("budget"):
            return False
        if not spec.get("lifecycle_actions"):
            return False
        if not spec.get("content_schema"):
            return False
    return _candidate_edge_permission_count(candidate) > 0


def _selector_input(policy_row: Dict[str, Any], candidate_row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    top = _top_candidate(candidate_row)
    return {
        "policy_input": policy_row["policy_input"],
        "candidate_count": len(candidate_row.get("candidates", [])) if candidate_row else 0,
        "top_candidate_available": top is not None,
        "top_candidate_rank": top.get("rank") if top else None,
        "top_candidate_support_count": top.get("support_count") if top else None,
        "top_candidate_prompt_node_roles": top.get("prompt_node_roles", []) if top else [],
        "top_candidate_prompt_node_spec_count": len(top.get("prompt_node_specs", [])) if top else 0,
        "top_candidate_edge_permission_count": _candidate_edge_permission_count(top),
        "top_candidate_lifecycle_action_count": _candidate_lifecycle_action_count(top),
        "top_candidate_decision_exposure_policy": top.get("decision_exposure_policy") if top else None,
    }


def _contains_forbidden_key(value: Any, forbidden: Iterable[str]) -> bool:
    forbidden_set = set(forbidden)
    if isinstance(value, dict):
        return any(key in forbidden_set or _contains_forbidden_key(child, forbidden_set) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item, forbidden_set) for item in value)
    return False


def build_template_plan_rows(
    r096_target_jsonl: str = DEFAULT_R096_TARGET_JSONL,
    r083_candidate_jsonl: str = DEFAULT_R083_CANDIDATE_JSONL,
) -> List[Dict[str, Any]]:
    targets = _load_jsonl(r096_target_jsonl)
    candidates = _candidate_index(r083_candidate_jsonl)
    rows = []
    for target in targets:
        candidate_row = candidates.get(target["task_id"])
        top = _top_candidate(candidate_row)
        should_switch = target["target_action"] == "switch_to_objective"
        selected = top if should_switch else None
        rows.append(
            {
                "task_id": target["task_id"],
                "selector_input": _selector_input(target, candidate_row),
                "target_action": target["target_action"],
                "target_reason": target["target_reason"],
                "target_prediction_source": target["target_prediction_source"],
                "selected_template": selected,
                "materialization_status": (
                    "template_attached"
                    if should_switch and selected
                    else "missing_required_template"
                    if should_switch
                    else "arg_fallback_no_template_needed"
                ),
                "requires_api_execution": bool(should_switch and selected),
                "has_update2_metadata": _has_update2_metadata(selected) if should_switch else False,
                "analysis": target["analysis"],
                "source_runs": ["R096", "R083"],
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_template_plan_summary() -> Dict[str, Any]:
    rows = build_template_plan_rows()
    switch_rows = [row for row in rows if row["target_action"] == "switch_to_objective"]
    attached_switch_rows = [
        row for row in switch_rows if row["materialization_status"] == "template_attached"
    ]
    missing_switch_rows = [
        row for row in switch_rows if row["materialization_status"] != "template_attached"
    ]
    selected_template_ranks = {
        row["task_id"]: row["selected_template"]["rank"]
        for row in attached_switch_rows
    }
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_rows": len(rows),
        "target_action_counts": dict(Counter(row["target_action"] for row in rows)),
        "switch_plan_count": len(switch_rows),
        "fallback_plan_count": len(rows) - len(switch_rows),
        "switch_target_tasks": [row["task_id"] for row in switch_rows],
        "switch_tasks_with_template_candidates": [row["task_id"] for row in attached_switch_rows],
        "missing_switch_template_tasks": [row["task_id"] for row in missing_switch_rows],
        "selected_template_ranks": selected_template_ranks,
        "clean_switch_target_tasks": [
            row["task_id"] for row in switch_rows if row["analysis"]["clean_label"] == "clean"
        ],
        "noisy_switch_target_tasks": [
            row["task_id"] for row in switch_rows if row["analysis"]["clean_label"] != "clean"
        ],
        "switch_targets_with_update2_metadata": sum(
            1 for row in switch_rows if row["has_update2_metadata"]
        ),
        "selector_input_field_violations": sum(
            1
            for row in rows
            if _contains_forbidden_key(row["selector_input"], FORBIDDEN_SELECTOR_INPUT_FIELDS)
        ),
        "forbidden_selector_input_fields": sorted(FORBIDDEN_SELECTOR_INPUT_FIELDS),
        "plan_jsonl": DEFAULT_PLAN_JSONL,
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    switch_rows = [row for row in summary["rows"] if row["target_action"] == "switch_to_objective"]
    table_rows = []
    for row in switch_rows:
        selected = row["selected_template"] or {}
        table_rows.append(
            "| `{task}` | `{label}` | `{reason}` | `{status}` | `{rank}` | `{support}` | `{roles}` | `{metadata}` |".format(
                task=row["task_id"],
                label=row["analysis"]["clean_label"],
                reason=row["target_reason"],
                status=row["materialization_status"],
                rank=selected.get("rank"),
                support=selected.get("support_count"),
                roles=",".join(selected.get("prompt_node_roles", [])),
                metadata=row["has_update2_metadata"],
            )
        )
    return "\n".join(
        [
            "# R097 Objective-Safety Template Plan",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Rows: `{summary['num_rows']}`",
            f"- Target action counts: `{summary['target_action_counts']}`",
            f"- Switch targets: `{summary['switch_target_tasks']}`",
            f"- Switch targets with template candidates: `{summary['switch_tasks_with_template_candidates']}`",
            f"- Missing switch templates: `{summary['missing_switch_template_tasks']}`",
            f"- Switch targets with update2 metadata: `{summary['switch_targets_with_update2_metadata']}`",
            f"- Selector input field violations: `{summary['selector_input_field_violations']}`",
            f"- Plan JSONL: `{summary['plan_jsonl']}`",
            "",
            "## Switch Plan",
            "",
            "| Task | Audit label | Target reason | Status | Template rank | Support | PN roles | Update2 metadata |",
            "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R097 attaches explicit R083 PromptNode graph templates to the R096 switch targets. "
            "The selector inputs exclude answer labels, correctness flags, task ids, target labels, "
            "and clean/noisy audit labels. This is an executable-plan bridge for a future API run, "
            "not a new accuracy result.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Join R096 policy targets with R083 PromptNode templates.")
    parser.add_argument("--plan-jsonl", default=DEFAULT_PLAN_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_template_plan_rows()
    _write_jsonl(args.plan_jsonl, rows)
    summary = build_template_plan_summary()
    summary["plan_jsonl"] = args.plan_jsonl
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R097 template plan: "
        f"rows={summary['num_rows']} switches={summary['switch_target_tasks']} "
        f"missing={summary['missing_switch_template_tasks']}"
    )


if __name__ == "__main__":
    main()
