import argparse
import json
import os
import sys
from types import SimpleNamespace
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from mas_framework.agents.prompt_node import PromptNode  # noqa: E402


RULE_NAME = "r138_router_repair_forwarding_prompt_hardening"
CLAIM_BOUNDARY = (
    "prompt-hardening protocol only; no API, accuracy, clean-recovery, "
    "transfer, robustness, or SCI-readiness claim"
)
DECISION_METHOD = "EdgePromptRepairContractFinalRefer"

ALLOWED_REPAIR_STATUS_VALUES = [
    "NUMERIC_NEAREST_WITH_TYPO_CHECK",
    "NUMERIC_TYPO_REPAIR",
    "SYMBOLIC_EQUIVALENCE_REPAIR",
]
SWITCH_TASKS = ["task_108", "task_250"]
FALLBACK_TASKS = ["task_8", "task_188"]

DEFAULT_R133_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r133_edge_prompt_policy_protocol_summary.json"
)
DEFAULT_R137_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r137_edge_prompt_repair_smoke_summary.json"
)
DEFAULT_TASK_SPLIT = (
    "experiment/aqua/task_split_aqua_tail34_r136_edge_prompt_repair_switches.json"
)
DEFAULT_OUTPUT_JSONL = (
    "experiment/aqua/aqua_tail34_r139_edge_prompt_repair_forwarding_switch_results.jsonl"
)
DEFAULT_SUMMARY_JSONL = (
    "experiment/aqua/res_logs/"
    "aqua_tail34_r139_edge_prompt_repair_forwarding_switch_summary.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/"
    "aqua_tail34_r138_router_repair_forwarding_prompt_hardening_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/"
    "aqua_tail34_r138_router_repair_forwarding_prompt_hardening_report.md"
)


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _prompt_output(role: str, predecessor_output: str) -> str:
    prompt_node = PromptNode(role=role, domain="aqua", llm_name="mock")
    prompt_node.spatial_predecessors = [
        SimpleNamespace(
            id="upstream",
            role="PN_Verifier" if role == "PN_Router" else "Math Solver",
            outputs=[predecessor_output],
        )
    ]
    return prompt_node.execute(
        {
            "task": (
                "How many children? Choices: A)1095961 B)1065961 "
                "C)1085961 D)1097961 E)1096061"
            )
        }
    )[0]


def build_evaluate_command(
    task_split_path: str = DEFAULT_TASK_SPLIT,
    output_file: str = DEFAULT_OUTPUT_JSONL,
    summary_log_file: str = DEFAULT_SUMMARY_JSONL,
) -> str:
    return (
        ".venv/bin/python experiment/aqua/evaluate_aqua.py "
        "--dataset_path datasets/AQuA/AQuA.jsonl "
        f"--task_split_path {task_split_path} "
        "--llm_name gpt-4o-2024-08-06 "
        f"--decision_method {DECISION_METHOD} "
        f"--output_file {output_file} "
        f"--summary_log_file {summary_log_file} "
        "--eval_batch_size 1 "
        "--forced_template_candidate_jsonl "
        "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl "
        "--forced_template_candidate_rank 5"
    )


def build_router_repair_forwarding_prompt_hardening(
    r133_summary: str = DEFAULT_R133_SUMMARY,
    r137_summary: str = DEFAULT_R137_SUMMARY,
) -> Dict[str, Any]:
    r133 = _load_json(r133_summary)
    r137 = _load_json(r137_summary)
    verifier_prompt = _prompt_output(
        "PN_Verifier",
        "Computed value 1096010; option E is 1096061 and no exact option is present.",
    )
    router_prompt = _prompt_output(
        "PN_Router",
        (
            "REPAIR_CANDIDATE_AUDIT: repair_option=E; "
            "repair_binding_status=NUMERIC_NEAREST_WITH_TYPO_CHECK; "
            "repair_confidence=0.93; repair_distance_ratio=0.000046."
        ),
    )
    return {
        "rule": RULE_NAME,
        "prompt_hardening_only": True,
        "no_api_run": True,
        "prompt_as_edge_first_class": bool(r133.get("prompt_as_edge_first_class")),
        "node_only_promptnode_sufficient": bool(
            r133.get("node_only_promptnode_sufficient")
        ),
        "edge_prompt_types": r133.get("edge_prompt_types") or [],
        "r137_forwarding_gap_confirmed": bool(
            r137.get("verifier_router_repair_forwarding_gap")
        ),
        "r137_task250_verifier_repair_candidate_present": bool(
            r137.get("task250_verifier_repair_candidate_present")
        ),
        "r137_task250_router_repair_forwarded": bool(
            r137.get("task250_router_repair_forwarded")
        ),
        "allowed_repair_status_values": list(ALLOWED_REPAIR_STATUS_VALUES),
        "pn_verifier_repair_status_values_hardened": all(
            status in verifier_prompt for status in ALLOWED_REPAIR_STATUS_VALUES
        ),
        "pn_verifier_forbids_exact_as_repair_status": (
            "never use EXACT_MATCH or EQUIVALENT_FORM as repair_binding_status"
            in verifier_prompt
        ),
        "pn_router_repair_forwarding_required": (
            "REPAIR_FORWARDING_REQUIRED" in router_prompt
        ),
        "router_supported_none_repair_coexistence": (
            "SUPPORTED_OPTION: NONE may coexist with REPAIR_OPTION" in router_prompt
        ),
        "pn_router_does_not_reset_repair_fields": (
            "do not reset repair fields to NONE" in router_prompt
        ),
        "no_task_id_routing": bool(r133.get("no_task_id_routing")),
        "multi_dataset_transfer_required": bool(
            r133.get("multi_dataset_transfer_required")
        ),
        "decision_method": DECISION_METHOD,
        "switch_tasks": list(SWITCH_TASKS),
        "fallback_tasks": list(FALLBACK_TASKS),
        "task_split_path": DEFAULT_TASK_SPLIT,
        "evaluate_command": build_evaluate_command(),
        "same_two_switch_task_smoke_allowed_next": True,
        "broad_api_allowed_next": False,
        "next_protocol": "bounded_router_repair_forwarding_api_smoke",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R138 Router Repair-Forwarding Prompt Hardening",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Prompt hardening only: `{summary['prompt_hardening_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Prompt as first-class edge: `{summary['prompt_as_edge_first_class']}`",
            f"- Node-only PromptNode sufficient: `{summary['node_only_promptnode_sufficient']}`",
            f"- R137 forwarding gap confirmed: `{summary['r137_forwarding_gap_confirmed']}`",
            "- PN_Verifier repair status values hardened: "
            f"`{summary['pn_verifier_repair_status_values_hardened']}`",
            "- PN_Verifier forbids exact/equivalent as repair status: "
            f"`{summary['pn_verifier_forbids_exact_as_repair_status']}`",
            "- PN_Router repair forwarding required: "
            f"`{summary['pn_router_repair_forwarding_required']}`",
            "- SUPPORTED_OPTION NONE can coexist with REPAIR_OPTION: "
            f"`{summary['router_supported_none_repair_coexistence']}`",
            "- PN_Router does not reset repair fields to NONE: "
            f"`{summary['pn_router_does_not_reset_repair_fields']}`",
            f"- No task-id routing: `{summary['no_task_id_routing']}`",
            "- Multi-dataset transfer still required: "
            f"`{summary['multi_dataset_transfer_required']}`",
            f"- Decision method: `{summary['decision_method']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            "- Same two-switch-task smoke allowed next: "
            f"`{summary['same_two_switch_task_smoke_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            "",
            "## Evaluate Command",
            "",
            "```bash",
            summary["evaluate_command"],
            "```",
            "",
            "## Interpretation",
            "",
            "R138 treats the repair prompt as an edge policy between PN_Verifier and "
            "PN_Router. It fixes the R137 interface gap by requiring the router to "
            "forward explicit verifier repair candidates even when the supported "
            "exact option remains NONE. This is not a result claim; it only permits "
            "one more bounded two-switch-task smoke before any broader evaluation.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write R138 router repair-forwarding prompt-hardening protocol."
    )
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_router_repair_forwarding_prompt_hardening()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R138 router repair-forwarding prompt hardening: "
        f"verifier={summary['pn_verifier_repair_status_values_hardened']} "
        f"router={summary['pn_router_repair_forwarding_required']} "
        f"broad={summary['broad_api_allowed_next']}"
    )


if __name__ == "__main__":
    main()
