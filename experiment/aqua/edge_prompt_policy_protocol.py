import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.clean_fix_graph_policy_selector_presmoke import (  # noqa: E402
    FORBIDDEN_SELECTOR_INPUT_FIELDS,
)
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r133_edge_prompt_policy_protocol"
CLAIM_BOUNDARY = (
    "protocol only; prompt-as-edge design and repair boundary, no API, accuracy, or cost result"
)

DEFAULT_R126_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r126_clean_fix_graph_policy_selector_protocol_summary.json"
)
DEFAULT_R127_PLAN_JSONL = "experiment/aqua/aqua_tail34_r127_clean_fix_graph_policy_selector_presmoke.jsonl"
DEFAULT_R132_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r132_deterministic_router_none_guard_smoke_summary.json"
)
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r133_edge_prompt_policy_protocol.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r133_edge_prompt_policy_protocol_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r133_edge_prompt_policy_protocol.md"

REQUIRED_EDGE_PROMPT_FIELDS = {
    "edge_prompt_type",
    "source_role",
    "target_role",
    "permissions",
    "prompt_contract",
    "option_binding_policy",
    "lifecycle_actions",
    "budget",
    "robustness_scope",
}

BASE_OPTION_BINDING_POLICY = [
    "exact_or_equivalent_option_only",
    "no_nearest_choice_without_repair_contract",
    "separate_official_label_accuracy_from_option_binding_correctness",
]

BASE_ROBUSTNESS_SCOPE = [
    "transfer_required",
    "dataset_agnostic_numeric_and_symbolic_binding",
    "no_task_id_routing",
    "no_true_answer_or_label_features",
]


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _ratio(count: int, total: int) -> str:
    return f"{int(count)}/{int(total)}"


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_SELECTOR_INPUT_FIELDS or _contains_forbidden_key(child):
                return True
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _edge_prompt_type(edge_record: Dict[str, Any]) -> str | None:
    source_role = edge_record.get("source_role")
    target_role = edge_record.get("target_role")
    permissions = set(edge_record.get("permissions") or [])
    if target_role == "PN_Memory" and "write" in permissions:
        return "evidence_write"
    if source_role == "PN_Memory" and target_role == "PN_Verifier":
        return "memory_to_verifier_read"
    if source_role == "PN_Verifier" and target_role == "PN_Router":
        return "verifier_to_router_forward"
    return None


def _contract_text(edge_prompt_type: str) -> str:
    contracts = {
        "evidence_write": (
            "Transmit computed values, candidate option labels, formulas, assumptions, and uncertainty "
            "into PN_Memory. Do not rewrite the task target and do not choose a nearest option."
        ),
        "memory_to_verifier_read": (
            "Expose only option-critical memory fields to PN_Verifier: target statement, computed value, "
            "candidate label, exact/equivalent match status, and conflicts."
        ),
        "verifier_to_router_forward": (
            "Forward a structured binding contract with SUPPORTED_OPTION, BINDING_STATUS, and conflict "
            "reason. Suppress unsupported labels and shifted-target evidence."
        ),
        "mismatch_repair_escalation": (
            "When no exact option exists, pass a repair record with numeric distance, possible typo class, "
            "and confidence. The router may not convert it into A-E unless the repair gate validates."
        ),
        "router_to_final_answer_contract": (
            "Return exactly one supported A-E option only when the router contract is exact/equivalent or "
            "a repair gate explicitly validates. Otherwise return abstention without parsable A-E text."
        ),
    }
    return contracts[edge_prompt_type]


def _edge_prompt_spec(
    edge_prompt_type: str,
    source_role: str,
    target_role: str,
    permissions: Sequence[str],
) -> Dict[str, Any]:
    return {
        "edge_prompt_type": edge_prompt_type,
        "source_role": source_role,
        "target_role": target_role,
        "permissions": list(permissions),
        "prompt_contract": _contract_text(edge_prompt_type),
        "option_binding_policy": list(BASE_OPTION_BINDING_POLICY),
        "lifecycle_actions": ["update", "compress", "prune"],
        "budget": {"max_tokens": 192, "max_updates": 2},
        "robustness_scope": list(BASE_ROBUSTNESS_SCOPE),
        "failure_policy": "abstain_or_escalate_to_repair_edge_before_final_option",
    }


def materialize_edge_prompt_specs(template: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    if not template:
        return []
    graph = template.get("graph") or {}
    specs: List[Dict[str, Any]] = []
    for edge_record in graph.get("edge_records") or []:
        edge_prompt_type = _edge_prompt_type(edge_record)
        if not edge_prompt_type:
            continue
        specs.append(
            _edge_prompt_spec(
                edge_prompt_type=edge_prompt_type,
                source_role=edge_record.get("source_role", ""),
                target_role=edge_record.get("target_role", ""),
                permissions=edge_record.get("permissions") or [],
            )
        )

    roles = list(graph.get("roles") or [])
    if "PN_Verifier" in roles and "PN_Router" in roles:
        specs.append(
            _edge_prompt_spec(
                edge_prompt_type="mismatch_repair_escalation",
                source_role="PN_Verifier",
                target_role="PN_Router",
                permissions=["read", "forward", "repair"],
            )
        )
    if "PN_Router" in roles:
        specs.append(
            _edge_prompt_spec(
                edge_prompt_type="router_to_final_answer_contract",
                source_role="PN_Router",
                target_role="FinalDecision",
                permissions=["forward"],
            )
        )
    return specs


def _has_repair_edge_prompt(specs: Sequence[Dict[str, Any]]) -> bool:
    return any(spec.get("edge_prompt_type") == "mismatch_repair_escalation" for spec in specs)


def _edge_prompt_selector_violation(specs: Sequence[Dict[str, Any]]) -> bool:
    return any(_contains_forbidden_key(spec) for spec in specs)


def build_edge_prompt_policy_protocol(
    r126_summary: str = DEFAULT_R126_SUMMARY,
    r127_plan_jsonl: str = DEFAULT_R127_PLAN_JSONL,
    r132_summary: str = DEFAULT_R132_SUMMARY,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    r126 = _load_json(r126_summary)
    r127_rows = _load_jsonl(r127_plan_jsonl)
    r132 = _load_json(r132_summary)

    rows: List[Dict[str, Any]] = []
    for row in r127_rows:
        selected_template = row.get("selected_template") or {}
        specs = materialize_edge_prompt_specs(selected_template)
        rows.append(
            {
                "task_id": row.get("task_id"),
                "planned_action": row.get("planned_action"),
                "selected_template_rank": row.get("selected_template_rank"),
                "edge_prompt_count": len(specs),
                "edge_prompt_specs": specs,
                "has_repair_edge_prompt": _has_repair_edge_prompt(specs),
                "edge_prompt_selector_input_violation": _edge_prompt_selector_violation(specs),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    switch_rows = [row for row in rows if row["planned_action"] == "switch_to_promptnode_template"]
    switch_count = len(switch_rows)
    all_edge_prompt_types = sorted(
        {
            spec["edge_prompt_type"]
            for row in rows
            for spec in row.get("edge_prompt_specs") or []
        }
    )
    forbidden_training_sources = list(r126.get("forbidden_training_sources") or [])
    forbidden_training_sources.extend(
        [
            "tail34_r132_switch_outputs",
            "tail34_r132_router_contracts",
            "tail34_r132_task250_prediction_or_truth",
        ]
    )
    summary = {
        "rule": RULE_NAME,
        "protocol_only": True,
        "no_api_run": True,
        "prompt_as_edge_first_class": True,
        "node_only_promptnode_sufficient": False,
        "allowed_training_sources": r126.get("allowed_training_sources") or [],
        "forbidden_training_sources": forbidden_training_sources,
        "uses_tail34_training_source": False,
        "r132_smoke_gate_passed": bool(r132.get("smoke_gate_passed")),
        "r132_exact_option_repair_required": bool(r132.get("exact_option_repair_required")),
        "switch_tasks": [row["task_id"] for row in switch_rows],
        "fallback_tasks": [
            row["task_id"] for row in rows if row["planned_action"] == "fallback_to_arg"
        ],
        "edge_prompt_schema_fields": sorted(REQUIRED_EDGE_PROMPT_FIELDS),
        "edge_prompt_types": all_edge_prompt_types,
        "switches_with_edge_prompt_specs": _ratio(
            sum(1 for row in switch_rows if row["edge_prompt_count"] > 0),
            switch_count,
        ),
        "switches_with_repair_edge_prompt": _ratio(
            sum(1 for row in switch_rows if row["has_repair_edge_prompt"]),
            switch_count,
        ),
        "edge_prompt_selector_input_violations": sum(
            1 for row in rows if row["edge_prompt_selector_input_violation"]
        ),
        "required_clean_harm_guards": r126.get("required_clean_harm_guards") or [],
        "required_clean_recovery_targets": r126.get("required_clean_recovery_targets") or [],
        "noisy_optional_targets": r126.get("noisy_optional_targets") or [],
        "multi_dataset_transfer_required": True,
        "no_task_id_routing": True,
        "broad_api_allowed_next": False,
        "next_protocol": "edge_prompt_exact_option_repair_protocol_before_api",
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return rows, summary


def render_report(rows: Sequence[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{action}` | `{rank}` | `{count}` | `{repair}` | `{violation}` |".format(
            task=row["task_id"],
            action=row["planned_action"],
            rank=row.get("selected_template_rank"),
            count=row["edge_prompt_count"],
            repair=row["has_repair_edge_prompt"],
            violation=row["edge_prompt_selector_input_violation"],
        )
        for row in rows
    ]
    return "\n".join(
        [
            "# R133 Edge-Prompt Policy Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Protocol only: `{summary['protocol_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Prompt as first-class edge: `{summary['prompt_as_edge_first_class']}`",
            f"- Node-only PromptNode sufficient: `{summary['node_only_promptnode_sufficient']}`",
            f"- Uses tail34 training source: `{summary['uses_tail34_training_source']}`",
            f"- R132 smoke gate passed: `{summary['r132_smoke_gate_passed']}`",
            f"- R132 exact-option repair required: `{summary['r132_exact_option_repair_required']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- Edge prompt schema fields: `{summary['edge_prompt_schema_fields']}`",
            f"- Edge prompt types: `{summary['edge_prompt_types']}`",
            f"- Switches with edge prompt specs: `{summary['switches_with_edge_prompt_specs']}`",
            f"- Switches with repair edge prompt: `{summary['switches_with_repair_edge_prompt']}`",
            f"- Edge-prompt selector input violations: `{summary['edge_prompt_selector_input_violations']}`",
            f"- Multi-dataset transfer required: `{summary['multi_dataset_transfer_required']}`",
            f"- No task-id routing: `{summary['no_task_id_routing']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "| Task | Planned action | Template rank | Edge prompts | Repair edge | Selector violation |",
            "| --- | --- | ---: | ---: | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R133 incorporates the prompt-as-edge constraint. The method direction is no longer just "
            "adding PromptNode roles; communication edges also carry contracts governing what evidence "
            "may be written, read, forwarded, repaired, or abstained. This directly addresses the R132 "
            "failure mode: abstention is integrity-preserving, but clean recovery requires a repair edge "
            "that is still label-free, auditable, and transfer-tested.",
            "",
            "This is a protocol artifact only. It blocks broad API expansion until the edge-prompt repair "
            "protocol is implemented and passes the same four-task clean gate.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R133 edge-prompt policy protocol.")
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows, summary = build_edge_prompt_policy_protocol()
    _write_jsonl(args.output_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(rows, summary))
    print(
        "Built R133 edge-prompt protocol: "
        f"switch_edge_specs={summary['switches_with_edge_prompt_specs']} "
        f"repair={summary['switches_with_repair_edge_prompt']} "
        f"broad_api={summary['broad_api_allowed_next']}"
    )


if __name__ == "__main__":
    main()
