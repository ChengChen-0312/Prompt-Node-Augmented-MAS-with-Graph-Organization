import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Sequence


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.selective_multiview_trigger import ratio_text, write_jsonl  # noqa: E402
from experiment.aqua.tail34_template_candidate_materialize import (  # noqa: E402
    FORBIDDEN_RUNTIME_FIELDS,
    record_has_forbidden_field,
)


RULE_NAME = "r123_explicit_promptnode_template_preflight"
CLAIM_BOUNDARY = (
    "preflight over explicit PromptNode template candidates; no API, accuracy, or cost result"
)

DEFAULT_CANDIDATE_JSONL = "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl"
DEFAULT_R097_PLAN_JSONL = "experiment/aqua/aqua_tail34_r097_objective_safety_template_plan.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r123_explicit_promptnode_template_preflight.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r123_explicit_promptnode_template_preflight_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r123_explicit_promptnode_template_preflight_report.md"
)

REGRESSION_TASKS = ["task_8", "task_108", "task_188", "task_250"]
REQUIRED_ROLES = {"PN_Memory", "PN_Router", "PN_Verifier"}
REQUIRED_IDENTITIES = {"Memory", "Instruction/Verifier", "Agent-like"}


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _candidate_index(path: str) -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_jsonl(path)}


def _r097_index(path: str) -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_jsonl(path)}


def _edge_permission_count(candidate: Dict[str, Any]) -> int:
    return len((candidate.get("graph") or {}).get("edge_permissions") or {})


def _lifecycle_action_count(candidate: Dict[str, Any]) -> int:
    return sum(len(spec.get("lifecycle_actions") or []) for spec in candidate.get("prompt_node_specs") or [])


def _has_update2_candidate_metadata(candidate: Dict[str, Any]) -> bool:
    roles = set(candidate.get("prompt_node_roles") or [])
    specs = candidate.get("prompt_node_specs") or []
    identities = {str(spec.get("identity_type")) for spec in specs}
    if not REQUIRED_ROLES.issubset(roles):
        return False
    if not REQUIRED_IDENTITIES.issubset(identities):
        return False
    if _edge_permission_count(candidate) <= 0:
        return False
    for spec in specs:
        if not spec.get("identity_type"):
            return False
        if not spec.get("insertion_pattern"):
            return False
        if not spec.get("content_schema"):
            return False
        if not spec.get("permissions"):
            return False
        if not spec.get("budget"):
            return False
        if not spec.get("lifecycle_actions"):
            return False
    return True


def _top_candidate(candidate_row: Dict[str, Any]) -> Dict[str, Any]:
    candidates = candidate_row.get("candidates") or []
    return candidates[0] if candidates else {}


def build_explicit_promptnode_template_preflight_rows(
    candidate_jsonl: str = DEFAULT_CANDIDATE_JSONL,
    r097_plan_jsonl: str = DEFAULT_R097_PLAN_JSONL,
    regression_tasks: Sequence[str] = REGRESSION_TASKS,
) -> List[Dict[str, Any]]:
    candidates = _candidate_index(candidate_jsonl)
    plan = _r097_index(r097_plan_jsonl)
    rows = []
    for task_id in regression_tasks:
        candidate_row = candidates.get(task_id, {})
        top = _top_candidate(candidate_row)
        plan_row = plan.get(task_id, {})
        target_action = plan_row.get("target_action")
        rows.append(
            {
                "task_id": task_id,
                "candidate_available": bool(candidate_row.get("candidates")),
                "candidate_count": len(candidate_row.get("candidates") or []),
                "top_candidate_rank": top.get("rank"),
                "top_candidate_support_count": top.get("support_count"),
                "top_candidate_graph_signature": top.get("graph_signature"),
                "top_candidate_promptnode_roles": sorted(top.get("prompt_node_roles") or []),
                "top_candidate_promptnode_spec_count": len(top.get("prompt_node_specs") or []),
                "top_candidate_edge_permission_count": _edge_permission_count(top),
                "top_candidate_lifecycle_action_count": _lifecycle_action_count(top),
                "top_candidate_has_update2_metadata": _has_update2_candidate_metadata(top)
                if top
                else False,
                "candidate_forbidden_field_violation": record_has_forbidden_field(
                    candidate_row, FORBIDDEN_RUNTIME_FIELDS
                )
                if candidate_row
                else False,
                "r097_target_action": target_action,
                "r097_materialization_status": plan_row.get("materialization_status"),
                "r097_requires_api_execution": bool(plan_row.get("requires_api_execution")),
                "r097_has_update2_metadata": bool(plan_row.get("has_update2_metadata")),
                "r097_target_reason": plan_row.get("target_reason"),
                "preflight_verdict": (
                    "explicit_template_candidate_ready_for_guarded_smoke"
                    if top and _has_update2_candidate_metadata(top)
                    else "missing_update2_template_candidate"
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_explicit_promptnode_template_preflight_summary(
    candidate_jsonl: str = DEFAULT_CANDIDATE_JSONL,
    r097_plan_jsonl: str = DEFAULT_R097_PLAN_JSONL,
) -> Dict[str, Any]:
    rows = build_explicit_promptnode_template_preflight_rows(candidate_jsonl, r097_plan_jsonl)
    total = len(rows)
    candidate_tasks = [row["task_id"] for row in rows if row["candidate_available"]]
    metadata_tasks = [row["task_id"] for row in rows if row["top_candidate_has_update2_metadata"]]
    violation_tasks = [row["task_id"] for row in rows if row["candidate_forbidden_field_violation"]]
    r097_api_tasks = [row["task_id"] for row in rows if row["r097_requires_api_execution"]]
    fallback_tasks = [
        row["task_id"]
        for row in rows
        if row["r097_target_action"] == "fallback_to_arg"
    ]
    top_roles = sorted(
        set().union(*(set(row["top_candidate_promptnode_roles"]) for row in rows))
    )
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "preflight_only": True,
        "no_api_run": True,
        "candidate_jsonl": candidate_jsonl,
        "r097_plan_jsonl": r097_plan_jsonl,
        "regression_tasks": list(REGRESSION_TASKS),
        "candidate_source_tasks": ratio_text(len(candidate_tasks), total),
        "candidate_tasks_with_update2_metadata": ratio_text(len(metadata_tasks), total),
        "candidate_tasks_with_forbidden_field_violations": ratio_text(len(violation_tasks), total),
        "top_candidate_promptnode_roles": top_roles,
        "r097_api_required_tasks": r097_api_tasks,
        "r097_fallback_tasks_in_regression_set": fallback_tasks,
        "broad_api_allowed_next": False,
        "same_four_task_smoke_allowed_next": (
            len(candidate_tasks) == total
            and len(metadata_tasks) == total
            and not violation_tasks
        ),
        "next_protocol": "same_four_task_explicit_template_guarded_smoke",
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{count}` | `{metadata}` | `{viol}` | `{action}` | `{api}` | `{support}` | `{roles}` |".format(
            task=row["task_id"],
            count=row["candidate_count"],
            metadata=row["top_candidate_has_update2_metadata"],
            viol=row["candidate_forbidden_field_violation"],
            action=row["r097_target_action"],
            api=row["r097_requires_api_execution"],
            support=row["top_candidate_support_count"],
            roles=",".join(row["top_candidate_promptnode_roles"]),
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R123 Explicit PromptNode Template Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Preflight only: `{summary['preflight_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Regression tasks: `{summary['regression_tasks']}`",
            f"- Candidate source tasks: `{summary['candidate_source_tasks']}`",
            f"- Candidate tasks with update2 metadata: `{summary['candidate_tasks_with_update2_metadata']}`",
            f"- Candidate forbidden-field violations: `{summary['candidate_tasks_with_forbidden_field_violations']}`",
            f"- Top candidate PromptNode roles: `{summary['top_candidate_promptnode_roles']}`",
            f"- R097 API-required tasks: `{summary['r097_api_required_tasks']}`",
            f"- R097 fallback tasks in regression set: `{summary['r097_fallback_tasks_in_regression_set']}`",
            f"- Same four-task smoke allowed next: `{summary['same_four_task_smoke_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "| Task | Candidates | Update2 metadata | Forbidden-field violation | R097 action | API required | Top support | PN roles |",
            "| --- | ---: | --- | --- | --- | --- | ---: | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R123 separates two facts that were conflated after R122. The R083 candidate pool does contain "
            "first-class PromptNode graph candidates for the four regression tasks, with identities, permissions, "
            "budgets, lifecycle actions, and no runtime-answer fields. However, the current R097 switch plan only "
            "attaches templates for `task_108` and `task_250`, so broad API evaluation remains blocked. The next "
            "permitted step is a same-four-task guarded smoke that records explicit template evidence on every "
            "candidate switch before any larger tail34 run.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preflight explicit PromptNode template evidence for the guarded four-task smoke."
    )
    parser.add_argument("--candidate-jsonl", default=DEFAULT_CANDIDATE_JSONL)
    parser.add_argument("--r097-plan-jsonl", default=DEFAULT_R097_PLAN_JSONL)
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_explicit_promptnode_template_preflight_rows(
        candidate_jsonl=args.candidate_jsonl,
        r097_plan_jsonl=args.r097_plan_jsonl,
    )
    summary = build_explicit_promptnode_template_preflight_summary(
        candidate_jsonl=args.candidate_jsonl,
        r097_plan_jsonl=args.r097_plan_jsonl,
    )
    summary["output_jsonl"] = args.output_jsonl
    write_jsonl(_repo_path(args.output_jsonl), rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R123 explicit PromptNode template preflight: "
        f"candidate_tasks={summary['candidate_source_tasks']} "
        f"metadata_tasks={summary['candidate_tasks_with_update2_metadata']} "
        f"same_four_task_smoke_allowed={summary['same_four_task_smoke_allowed_next']}"
    )


if __name__ == "__main__":
    main()
