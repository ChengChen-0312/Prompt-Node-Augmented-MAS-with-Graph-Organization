import argparse
import json
import os
import sys
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r099_task250_template_rank_sweep_protocol"
CLAIM_BOUNDARY = "pre-registered task250 rank2-5 template sweep; no result or accuracy claim"

DEFAULT_TASK_SPLIT = "experiment/aqua/task_split_aqua_tail34_task250_smoke.json"
DEFAULT_CANDIDATE_JSONL = "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl"
DEFAULT_PROTOCOL_JSON = "experiment/aqua/res_logs/aqua_tail34_r099_task250_template_rank_sweep_protocol.json"
DEFAULT_PROTOCOL_MD = "experiment/aqua/run_logs/aqua_tail34_r099_task250_template_rank_sweep_protocol.md"


def _rank_output_file(rank: int) -> str:
    return f"experiment/aqua/aqua_tail34_r100_forced_template_rank{rank}_task250_results.jsonl"


def _rank_summary_file(rank: int) -> str:
    return f"experiment/aqua/res_logs/aqua_tail34_r100_forced_template_rank{rank}_task250_summary.jsonl"


def _rank_command(rank: int, protocol: Dict[str, Any]) -> str:
    return (
        ".venv/bin/python experiment/aqua/evaluate_aqua.py "
        "--dataset_path datasets/AQuA/AQuA.jsonl "
        f"--task_split_path {protocol['task_split_path']} "
        f"--llm_name {protocol['model']} "
        "--decision_method RouterContractFinalRefer "
        f"--output_file {_rank_output_file(rank)} "
        f"--summary_log_file {_rank_summary_file(rank)} "
        "--eval_batch_size 1 "
        f"--forced_template_candidate_jsonl {protocol['forced_template_candidate_jsonl']} "
        f"--forced_template_candidate_rank {rank}"
    )


def build_protocol() -> Dict[str, Any]:
    protocol = {
        "rule": RULE_NAME,
        "task_id": "task_250",
        "task_split_path": DEFAULT_TASK_SPLIT,
        "task_split_indices": [250],
        "num_tasks": 1,
        "is_full_tail34": False,
        "model": "gpt-4o-2024-08-06",
        "forced_template_candidate_jsonl": DEFAULT_CANDIDATE_JSONL,
        "sweep_ranks": [2, 3, 4, 5],
        "excluded_ranks": [1],
        "excluded_rank_reason": "R098 shows rank1 predicts A and does not reproduce the clean task250 target.",
        "desired_prediction": "E",
        "success_gate": {
            "minimum_matching_rank_count": 1,
            "required_prediction": "E",
            "no_full_tail34_claim": True,
            "next_step_if_success": "freeze matching rank for a tiny clean-safe smoke before broader validation",
            "next_step_if_fail": "return to graph-policy/template generation; do not run full tail34",
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }
    protocol["rank_outputs"] = [
        {
            "rank": rank,
            "output_file": _rank_output_file(rank),
            "summary_log_file": _rank_summary_file(rank),
            "command": _rank_command(rank, protocol),
        }
        for rank in protocol["sweep_ranks"]
    ]
    return protocol


def render_protocol(protocol: Dict[str, Any]) -> str:
    command_lines = []
    for item in protocol["rank_outputs"]:
        command_lines.extend(
            [
                f"### Rank {item['rank']}",
                "",
                "```bash",
                item["command"],
                "```",
                "",
            ]
        )
    return "\n".join(
        [
            "# R099 Task250 Template Rank Sweep Protocol",
            "",
            f"**Claim boundary**: {protocol['claim_boundary']}",
            "",
            f"- Task: `{protocol['task_id']}`",
            f"- Split: `{protocol['task_split_path']}` with indices `{protocol['task_split_indices']}`",
            f"- Model: `{protocol['model']}`",
            f"- Candidate file: `{protocol['forced_template_candidate_jsonl']}`",
            f"- Sweep ranks: `{protocol['sweep_ranks']}`",
            f"- Excluded ranks: `{protocol['excluded_ranks']}`",
            f"- Desired prediction: `{protocol['desired_prediction']}`",
            f"- Full tail34: `{protocol['is_full_tail34']}`",
            "",
            "## Frozen Commands",
            "",
            *command_lines,
            "## Interpretation Rule",
            "",
            "This protocol is only allowed to test whether a non-rank1 explicit PromptNode template can "
            "recover the clean R095 `task_250` switch. It does not establish held-out accuracy.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pre-register task250 rank2-rank5 forced-template sweep.")
    parser.add_argument("--protocol-json", default=DEFAULT_PROTOCOL_JSON)
    parser.add_argument("--protocol-md", default=DEFAULT_PROTOCOL_MD)
    parser.add_argument("--task-split", default=DEFAULT_TASK_SPLIT)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    protocol = build_protocol()
    protocol["task_split_path"] = args.task_split
    os.makedirs(os.path.dirname(_repo_path(args.task_split)), exist_ok=True)
    write_json(_repo_path(args.task_split), {"test_indices": protocol["task_split_indices"]})
    write_json(_repo_path(args.protocol_json), protocol)
    write_text(_repo_path(args.protocol_md), render_protocol(protocol))
    print(
        "Built R099 task250 rank sweep protocol: "
        f"ranks={protocol['sweep_ranks']} desired={protocol['desired_prediction']}"
    )


if __name__ == "__main__":
    main()
