import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import mas_framework.agents  # noqa: F401,E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from mas_framework.agents.agent_registry import AgentRegistry  # noqa: E402
from mas_framework.agents.final_decision import (  # noqa: E402
    select_calibrated_edge_prompt_repair_answer,
)


RULE_NAME = "r144_calibrated_repair_final_gate_implementation_presmoke"
CLAIM_BOUNDARY = (
    "implementation pre-smoke only; no API, accuracy, broad evaluation, "
    "transfer, robustness, or SCI-readiness claim"
)
DECISION_METHOD = "CalibratedEdgePromptRepairContractFinalRefer"

DEFAULT_R143_SUMMARY = (
    "experiment/aqua/res_logs/"
    "aqua_tail34_r143_calibrated_repair_final_gate_offline_replay_summary.json"
)
DEFAULT_TASK_SPLIT = (
    "experiment/aqua/task_split_aqua_tail34_r136_edge_prompt_repair_switches.json"
)
DEFAULT_OUTPUT_JSONL = (
    "experiment/aqua/aqua_tail34_r146_calibrated_repair_switch_results.jsonl"
)
DEFAULT_SUMMARY_JSONL = (
    "experiment/aqua/res_logs/aqua_tail34_r146_calibrated_repair_switch_summary.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/"
    "aqua_tail34_r144_calibrated_repair_final_gate_implementation_presmoke_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/"
    "aqua_tail34_r144_calibrated_repair_final_gate_implementation_presmoke.md"
)


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _close_forwarded_repair_spatial_info() -> Dict[str, Any]:
    return {
        "router": {
            "role": "PN_Router",
            "output": (
                "SUPPORTED_OPTION: NONE\n"
                "BINDING_STATUS: NO_EXACT_OPTION\n"
                "REPAIR_OPTION: E\n"
                "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                "REPAIR_CONFIDENCE: 0.50\n"
                "REPAIR_DISTANCE_RATIO: 0.000046\n"
            ),
        }
    }


def _direct_contradiction_spatial_info() -> Dict[str, Any]:
    spatial_info = _close_forwarded_repair_spatial_info()
    spatial_info.update(
        {
            "solver_a": {"role": "MathSolver", "output": "The answer is D"},
            "solver_b": {"role": "Inspector", "output": "The answer is D"},
        }
    )
    return spatial_info


def _large_distance_spatial_info() -> Dict[str, Any]:
    return {
        "router": {
            "role": "PN_Router",
            "output": (
                "SUPPORTED_OPTION: NONE\n"
                "BINDING_STATUS: NO_EXACT_OPTION\n"
                "REPAIR_OPTION: E\n"
                "REPAIR_BINDING_STATUS: NUMERIC_NEAREST_WITH_TYPO_CHECK\n"
                "REPAIR_CONFIDENCE: 0.50\n"
                "REPAIR_DISTANCE_RATIO: 0.03\n"
            ),
        }
    }


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


def build_calibrated_repair_final_gate_implementation_presmoke(
    r143_summary: str = DEFAULT_R143_SUMMARY,
) -> Dict[str, Any]:
    r143 = _load_json(r143_summary)
    agent = AgentRegistry.get(DECISION_METHOD, domain="aqua", llm_name="mock")
    task = {"task": "Q Choices: A)1 B)2 C)3 D)4 E)5"}
    close_forwarded_prediction = agent._execute(
        task, _close_forwarded_repair_spatial_info(), {}
    )
    return {
        "rule": RULE_NAME,
        "presmoke_only": True,
        "no_api_run": True,
        "decision_method": DECISION_METHOD,
        "decision_method_registered": agent.agent_name == DECISION_METHOD,
        "close_forwarded_repair_accepted": (
            select_calibrated_edge_prompt_repair_answer(
                _close_forwarded_repair_spatial_info()
            )
            == "E"
            and close_forwarded_prediction == "The answer is E"
        ),
        "direct_contradiction_rejected": (
            select_calibrated_edge_prompt_repair_answer(
                _direct_contradiction_spatial_info()
            )
            is None
        ),
        "large_distance_rejected": (
            select_calibrated_edge_prompt_repair_answer(_large_distance_spatial_info())
            is None
        ),
        "r143_offline_gate_passed": bool(
            r143.get("same_four_task_gate_offline_passed")
        ),
        "r143_calibrated_selected_accuracy": r143.get("calibrated_selected_accuracy"),
        "r143_clean_fix_harm": r143.get("clean_fix_harm"),
        "task_split_path": DEFAULT_TASK_SPLIT,
        "evaluate_command": build_evaluate_command(),
        "same_two_switch_task_smoke_allowed_next": True,
        "r145_goal_audit_required_before_api": True,
        "broad_api_allowed_next": False,
        "next_protocol": "r145_goal_audit_before_calibrated_api_smoke",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R144 Calibrated Repair Final-Gate Implementation Pre-Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Pre-smoke only: `{summary['presmoke_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Decision method: `{summary['decision_method']}`",
            f"- Decision method registered: `{summary['decision_method_registered']}`",
            f"- Close forwarded repair accepted: `{summary['close_forwarded_repair_accepted']}`",
            f"- Direct contradiction rejected: `{summary['direct_contradiction_rejected']}`",
            f"- Large distance rejected: `{summary['large_distance_rejected']}`",
            f"- R143 offline gate passed: `{summary['r143_offline_gate_passed']}`",
            f"- Same two-switch-task smoke allowed next: `{summary['same_two_switch_task_smoke_allowed_next']}`",
            f"- R145 goal audit required before API: `{summary['r145_goal_audit_required_before_api']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Evaluate Command After R145 Audit",
            "",
            "```bash",
            summary["evaluate_command"],
            "```",
            "",
            "## Interpretation",
            "",
            "R144 registers the calibrated repair final decision method and verifies its "
            "local accept/reject behavior. Because the user's five-run audit rule is active, "
            "the R145 goal audit must run before launching the bounded API smoke.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write R144 calibrated repair final-gate implementation pre-smoke."
    )
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_calibrated_repair_final_gate_implementation_presmoke()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R144 calibrated repair final-gate pre-smoke: "
        f"registered={summary['decision_method_registered']} "
        f"r145_required={summary['r145_goal_audit_required_before_api']}"
    )


if __name__ == "__main__":
    main()
