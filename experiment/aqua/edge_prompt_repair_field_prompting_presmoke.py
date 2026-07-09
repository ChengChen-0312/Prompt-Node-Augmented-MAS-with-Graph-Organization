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


RULE_NAME = "r136_edge_prompt_repair_field_prompting_presmoke"
CLAIM_BOUNDARY = "pre-smoke protocol only; prompt-field update, no API, accuracy, cost, transfer, or robustness result"
DECISION_METHOD = "EdgePromptRepairContractFinalRefer"

REPAIR_FIELD_NAMES = [
    "REPAIR_OPTION",
    "REPAIR_BINDING_STATUS",
    "REPAIR_CONFIDENCE",
    "REPAIR_DISTANCE_RATIO",
]
SWITCH_TASK_INDICES = [108, 250]
SWITCH_TASKS = ["task_108", "task_250"]
FALLBACK_TASKS = ["task_8", "task_188"]

DEFAULT_R134_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r134_edge_prompt_repair_gate_protocol_summary.json"
)
DEFAULT_R135_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r135_goal_audit_summary.json"
DEFAULT_TASK_SPLIT = "experiment/aqua/task_split_aqua_tail34_r136_edge_prompt_repair_switches.json"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r136_edge_prompt_repair_field_prompting_presmoke_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r136_edge_prompt_repair_field_prompting_presmoke_report.md"
)
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r136_edge_prompt_repair_switch_results.jsonl"
DEFAULT_FORCED_SUMMARY_JSONL = (
    "experiment/aqua/res_logs/aqua_tail34_r136_edge_prompt_repair_switch_summary.jsonl"
)


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _prompt_output(role: str, predecessor_output: str) -> str:
    prompt_node = PromptNode(role=role, domain="aqua", llm_name="mock")
    prompt_node.spatial_predecessors = [
        SimpleNamespace(id="upstream", role="PN_Verifier" if role == "PN_Router" else "Math Solver", outputs=[predecessor_output])
    ]
    return prompt_node.execute(
        {
            "task": (
                "How many children? Choices: A)1095961 B)1065961 "
                "C)1085961 D)1097961 E)1096061"
            )
        }
    )[0]


def write_switch_task_split(path: str = DEFAULT_TASK_SPLIT) -> Dict[str, Any]:
    payload = {"test_indices": list(SWITCH_TASK_INDICES)}
    write_json(_repo_path(path), payload)
    return payload


def build_evaluate_command(
    task_split_path: str = DEFAULT_TASK_SPLIT,
    output_file: str = DEFAULT_OUTPUT_JSONL,
    summary_log_file: str = DEFAULT_FORCED_SUMMARY_JSONL,
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
        "--forced_template_candidate_jsonl experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl "
        "--forced_template_candidate_rank 5"
    )


def build_edge_prompt_repair_field_prompting_presmoke(
    r134_summary: str = DEFAULT_R134_SUMMARY,
    r135_summary: str = DEFAULT_R135_SUMMARY,
) -> Dict[str, Any]:
    r134 = _load_json(r134_summary)
    r135 = _load_json(r135_summary)
    verifier_prompt = _prompt_output(
        "PN_Verifier",
        "Computed value 1096010; option E is 1096061 and no exact option is present.",
    )
    router_prompt = _prompt_output(
        "PN_Router",
        "REPAIR_CANDIDATE_AUDIT: repair_option=E; repair_confidence=0.93; repair_distance_ratio=0.000046.",
    )
    return {
        "rule": RULE_NAME,
        "presmoke_only": True,
        "no_api_run": True,
        "pn_verifier_repair_audit_prompted": all(
            token in verifier_prompt
            for token in [
                "REPAIR_CANDIDATE_AUDIT",
                "repair_option",
                "repair_confidence",
                "repair_distance_ratio",
            ]
        ),
        "pn_router_repair_fields_prompted": all(
            token in router_prompt for token in REPAIR_FIELD_NAMES
        ),
        "repair_field_names": list(REPAIR_FIELD_NAMES),
        "r134_repair_gate_ready": (
            r134.get("decision_method") == DECISION_METHOD
            and r134.get("explicit_repair_parser_prediction") == "E"
            and r134.get("missing_repair_parser_prediction") == "None."
        ),
        "r135_status": r135.get("status"),
        "r135_clean_gate_still_not_met": bool(r135.get("clean_gate_still_not_met")),
        "decision_method": DECISION_METHOD,
        "switch_tasks": list(SWITCH_TASKS),
        "fallback_tasks": list(FALLBACK_TASKS),
        "task_split_path": DEFAULT_TASK_SPLIT,
        "evaluate_command": build_evaluate_command(),
        "same_four_task_smoke_allowed_next": True,
        "broad_api_allowed_next": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R136 Edge-Prompt Repair-Field Prompting Pre-Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Pre-smoke only: `{summary['presmoke_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- PN_Verifier repair audit prompted: `{summary['pn_verifier_repair_audit_prompted']}`",
            f"- PN_Router repair fields prompted: `{summary['pn_router_repair_fields_prompted']}`",
            f"- Repair field names: `{summary['repair_field_names']}`",
            f"- R134 repair gate ready: `{summary['r134_repair_gate_ready']}`",
            f"- R135 status: `{summary['r135_status']}`",
            f"- R135 clean gate still not met: `{summary['r135_clean_gate_still_not_met']}`",
            f"- Decision method: `{summary['decision_method']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- Task split path: `{summary['task_split_path']}`",
            f"- Same-four-task smoke allowed next: `{summary['same_four_task_smoke_allowed_next']}`",
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
            "R136 updates the PromptNode prompt path so PN_Verifier can produce a repair-candidate audit "
            "and PN_Router can emit the machine-readable repair fields consumed by R134. This is still "
            "pre-smoke only. The next API step is bounded to the two switch tasks with ARG fallback guards "
            "on task_8 and task_188.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R136 repair-field prompting pre-smoke.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    write_switch_task_split()
    summary = build_edge_prompt_repair_field_prompting_presmoke()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R136 repair-field prompting pre-smoke: "
        f"verifier={summary['pn_verifier_repair_audit_prompted']} "
        f"router={summary['pn_router_repair_fields_prompted']} "
        f"same_four={summary['same_four_task_smoke_allowed_next']}"
    )


if __name__ == "__main__":
    main()
