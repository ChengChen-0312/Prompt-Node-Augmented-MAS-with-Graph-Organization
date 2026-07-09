import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_bad_exact_gate import build_bad_exact_features  # noqa: E402
from experiment.aqua.forced_template_smoke_gate import FORBIDDEN_DECISION_FIELDS  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r092_forced_template_tail34_validation_protocol"
CLAIM_BOUNDARY = "pre-registered full tail34 forced-template validation protocol, not a result"

DEFAULT_PROTOCOL_JSON = "experiment/aqua/res_logs/aqua_tail34_r092_forced_template_validation_protocol.json"
DEFAULT_PROTOCOL_MD = "experiment/aqua/run_logs/aqua_tail34_r092_forced_template_validation_protocol.md"

DEFAULT_DATASET_PATH = "datasets/AQuA/AQuA.jsonl"
DEFAULT_TASK_SPLIT = "experiment/aqua/task_split_aqua_tail34.json"
DEFAULT_CANDIDATE_JSONL = "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl"
DEFAULT_FORCED_OUTPUT = "experiment/aqua/aqua_tail34_r092_forced_template_rank1_results.jsonl"
DEFAULT_FORCED_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r092_forced_template_rank1_summary.jsonl"
DEFAULT_GATE_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r092_bad_exact_gate_forced_tail34_summary.json"
DEFAULT_GATE_REPORT = "experiment/aqua/run_logs/aqua_tail34_r092_bad_exact_gate_forced_tail34_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _count_split_tasks(split_path: str) -> int:
    with open(_repo_path(split_path), "r", encoding="utf-8") as f:
        split = json.load(f)
    return len(split["test_indices"])


def build_validation_protocol() -> Dict[str, Any]:
    decision_feature_fields = sorted(build_bad_exact_features({}).keys())
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "pre_registered_before_full_run",
        "dataset_path": DEFAULT_DATASET_PATH,
        "task_split_path": DEFAULT_TASK_SPLIT,
        "num_tasks": _count_split_tasks(DEFAULT_TASK_SPLIT),
        "llm_name": "gpt-4o-2024-08-06",
        "decision_method": "RouterContractFinalRefer",
        "forced_template_candidate_jsonl": DEFAULT_CANDIDATE_JSONL,
        "forced_template_rank": 1,
        "forced_template_output_file": DEFAULT_FORCED_OUTPUT,
        "forced_template_summary_log_file": DEFAULT_FORCED_SUMMARY,
        "gate_rule": "r088_bad_exact_contract_gate",
        "gate_summary_json": DEFAULT_GATE_SUMMARY,
        "gate_report_md": DEFAULT_GATE_REPORT,
        "baseline_results": "experiment/aqua/aqua_tail34_arg_baseline_results.jsonl",
        "baseline_accuracy_reference": "28/34",
        "decision_feature_fields": decision_feature_fields,
        "forbidden_outcome_fields": sorted(FORBIDDEN_DECISION_FIELDS),
        "success_gate": {
            "minimum_gate_solved": ">=29/34",
            "maximum_harm": 0,
            "required_decision_field_violations": 0,
            "required_same_model": "gpt-4o-2024-08-06",
        },
        "failure_interpretation": (
            "If the frozen gate does not beat ARG or introduces harm, forced rank-1 templates "
            "are not ready as a paper main result; move back to template selection or graph-policy training."
        ),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_protocol(protocol: Dict[str, Any]) -> str:
    command = (
        ".venv/bin/python experiment/aqua/evaluate_aqua.py "
        f"--dataset_path {protocol['dataset_path']} "
        f"--task_split_path {protocol['task_split_path']} "
        f"--llm_name {protocol['llm_name']} "
        f"--decision_method {protocol['decision_method']} "
        f"--output_file {protocol['forced_template_output_file']} "
        f"--summary_log_file {protocol['forced_template_summary_log_file']} "
        "--eval_batch_size 1 "
        f"--forced_template_candidate_jsonl {protocol['forced_template_candidate_jsonl']} "
        f"--forced_template_candidate_rank {protocol['forced_template_rank']}"
    )
    return "\n".join(
        [
            "# R092 Forced-Template Tail34 Validation Protocol",
            "",
            f"**Claim boundary**: {protocol['claim_boundary']}",
            "",
            f"- Status: `{protocol['status']}`",
            f"- Split: `{protocol['task_split_path']}` (`{protocol['num_tasks']}` tasks)",
            f"- Model: `{protocol['llm_name']}`",
            f"- Forced-template candidate file: `{protocol['forced_template_candidate_jsonl']}`",
            f"- Forced-template rank: `{protocol['forced_template_rank']}`",
            f"- Frozen gate: `{protocol['gate_rule']}`",
            f"- ARG baseline reference: `{protocol['baseline_accuracy_reference']}`",
            f"- Success gate: `{protocol['success_gate']}`",
            f"- Forbidden decision fields: `{protocol['forbidden_outcome_fields']}`",
            "",
            "## Frozen Run Command",
            "",
            "```bash",
            command,
            "```",
            "",
            "## Interpretation Rule",
            "",
            protocol["failure_interpretation"],
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write the R092 forced-template validation protocol.")
    parser.add_argument("--protocol-json", default=DEFAULT_PROTOCOL_JSON)
    parser.add_argument("--protocol-md", default=DEFAULT_PROTOCOL_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    protocol = build_validation_protocol()
    write_json(_repo_path(args.protocol_json), protocol)
    write_text(_repo_path(args.protocol_md), render_protocol(protocol))
    print(
        "Built R092 protocol: "
        f"{protocol['num_tasks']} tasks, model={protocol['llm_name']}, gate={protocol['gate_rule']}"
    )


if __name__ == "__main__":
    main()
