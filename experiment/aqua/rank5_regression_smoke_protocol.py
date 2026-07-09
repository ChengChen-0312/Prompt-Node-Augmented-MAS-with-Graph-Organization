import argparse
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r105_rank5_regression_smoke_protocol"
CLAIM_BOUNDARY = "pre-registered four-task rank5 regression smoke for consensus check; no held-out accuracy claim"

DEFAULT_TASK_SPLIT = "experiment/aqua/task_split_aqua_tail34_r105_rank5_regression_smoke.json"
DEFAULT_PROTOCOL_JSON = "experiment/aqua/res_logs/aqua_tail34_r105_rank5_regression_smoke_protocol.json"
DEFAULT_PROTOCOL_MD = "experiment/aqua/run_logs/aqua_tail34_r105_rank5_regression_smoke_protocol.md"
DEFAULT_CANDIDATE_JSONL = "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl"
DEFAULT_OUTPUT = "experiment/aqua/aqua_tail34_r106_rank5_regression_smoke_results.jsonl"
DEFAULT_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r106_rank5_regression_smoke_summary.jsonl"


def build_protocol() -> Dict[str, Any]:
    protocol = {
        "rule": RULE_NAME,
        "selected_rank": 5,
        "comparison_rank": 2,
        "task_split_path": DEFAULT_TASK_SPLIT,
        "task_split_indices": [8, 108, 188, 250],
        "num_tasks": 4,
        "is_full_tail34": False,
        "clean_harm_guard_tasks": ["task_8", "task_188"],
        "clean_recovery_targets": ["task_250"],
        "noisy_optional_targets": ["task_108"],
        "model": "gpt-4o-2024-08-06",
        "forced_template_candidate_jsonl": DEFAULT_CANDIDATE_JSONL,
        "output_file": DEFAULT_OUTPUT,
        "summary_log_file": DEFAULT_SUMMARY,
        "success_gate": {
            "clean_harm_guard_harms": 0,
            "rank2_rank5_consensus_on_clean_recovery": True,
            "no_full_tail34_claim": True,
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }
    protocol["command"] = (
        ".venv/bin/python experiment/aqua/evaluate_aqua.py "
        "--dataset_path datasets/AQuA/AQuA.jsonl "
        f"--task_split_path {protocol['task_split_path']} "
        f"--llm_name {protocol['model']} "
        "--decision_method RouterContractFinalRefer "
        f"--output_file {protocol['output_file']} "
        f"--summary_log_file {protocol['summary_log_file']} "
        "--eval_batch_size 1 "
        f"--forced_template_candidate_jsonl {protocol['forced_template_candidate_jsonl']} "
        f"--forced_template_candidate_rank {protocol['selected_rank']}"
    )
    return protocol


def render_protocol(protocol: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R105 Rank5 Regression Smoke Protocol",
            "",
            f"**Claim boundary**: {protocol['claim_boundary']}",
            "",
            f"- Selected rank: `{protocol['selected_rank']}`",
            f"- Comparison rank: `{protocol['comparison_rank']}`",
            f"- Split: `{protocol['task_split_path']}` with indices `{protocol['task_split_indices']}`",
            f"- Clean harm guards: `{protocol['clean_harm_guard_tasks']}`",
            f"- Clean recovery targets: `{protocol['clean_recovery_targets']}`",
            f"- Model: `{protocol['model']}`",
            f"- Full tail34: `{protocol['is_full_tail34']}`",
            "",
            "## Frozen Command",
            "",
            "```bash",
            protocol["command"],
            "```",
            "",
            "## Interpretation Rule",
            "",
            "This smoke tests whether rank5 can provide a cleaner partner for rank2-style evidence. "
            "It cannot establish held-out accuracy.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pre-register rank5 regression smoke for consensus check.")
    parser.add_argument("--protocol-json", default=DEFAULT_PROTOCOL_JSON)
    parser.add_argument("--protocol-md", default=DEFAULT_PROTOCOL_MD)
    parser.add_argument("--task-split", default=DEFAULT_TASK_SPLIT)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    protocol = build_protocol()
    protocol["task_split_path"] = args.task_split
    write_json(_repo_path(args.task_split), {"test_indices": protocol["task_split_indices"]})
    write_json(_repo_path(args.protocol_json), protocol)
    write_text(_repo_path(args.protocol_md), render_protocol(protocol))
    print(
        "Built R105 rank5 regression smoke protocol: "
        f"indices={protocol['task_split_indices']} rank={protocol['selected_rank']}"
    )


if __name__ == "__main__":
    main()
