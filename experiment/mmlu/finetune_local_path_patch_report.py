import argparse
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.mmlu import finetune_mmlu  # noqa: E402


RULE_NAME = "r157_mmlu_finetune_local_path_patch"
CLAIM_BOUNDARY = (
    "finetune local-path patch only; no API run, no checkpoint training, "
    "no transfer result, and no SCI-Q2 readiness claim"
)

DEFAULT_R156_SUMMARY = (
    "experiment/mmlu/res_logs/mmlu_r156_checkpoint_build_dry_run_or_import_validation_summary.json"
)
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r157_finetune_local_path_patch_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r157_finetune_local_path_patch.md"
FINETUNE_SCRIPT = "experiment/mmlu/finetune_mmlu.py"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _read_text(path: str) -> str:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return f.read()


def build_patch_summary() -> Dict[str, Any]:
    custom_args = finetune_mmlu.parse_cli_args(
        [
            "--cold_start_dir",
            "experiment/ColdStartData_mmlu",
            "--finetune_data_dir",
            "experiment/FinetuneData_mmlu",
            "--task_split_file",
            "experiment/mmlu/task_split_mmlu.json",
        ]
    )
    default_args = finetune_mmlu.parse_cli_args([])
    source = _read_text(FINETUNE_SCRIPT)
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_dry_run": DEFAULT_R156_SUMMARY,
        "no_api_run": True,
        "parse_cli_accepts_local_paths": (
            custom_args.cold_start_dir == "experiment/ColdStartData_mmlu"
            and custom_args.finetune_data_dir == "experiment/FinetuneData_mmlu"
            and custom_args.task_split_file == "experiment/mmlu/task_split_mmlu.json"
        ),
        "default_paths_are_local": (
            "/root/ARG-Designer" not in default_args.cold_start_dir
            and "/root/ARG-Designer" not in default_args.finetune_data_dir
            and default_args.task_split_file.endswith("experiment/mmlu/task_split_mmlu.json")
        ),
        "default_cold_start_dir": default_args.cold_start_dir,
        "default_finetune_data_dir": default_args.finetune_data_dir,
        "default_task_split_file": default_args.task_split_file,
        "hardcoded_root_argdesigner_removed": "/root/ARG-Designer" not in source,
        "checkpoint_training_run": False,
        "transfer_api_allowed_next": False,
        "broad_api_allowed_next": False,
        "next_protocol": "r158_mmlu_checkpoint_build_dry_run_after_path_patch",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R157 MMLU Finetune Local Path Patch",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- No API run: `{summary['no_api_run']}`",
            f"- CLI accepts local paths: `{summary['parse_cli_accepts_local_paths']}`",
            f"- Default paths are local: `{summary['default_paths_are_local']}`",
            f"- Default cold-start dir: `{summary['default_cold_start_dir']}`",
            f"- Default finetune data dir: `{summary['default_finetune_data_dir']}`",
            f"- Default task split file: `{summary['default_task_split_file']}`",
            f"- Hardcoded `/root/ARG-Designer` removed: `{summary['hardcoded_root_argdesigner_removed']}`",
            f"- Checkpoint training run: `{summary['checkpoint_training_run']}`",
            f"- Transfer API allowed next: `{summary['transfer_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Interpretation",
            "",
            "R157 removes the local path blocker identified by R156 from `finetune_mmlu.py`. "
            "It does not run cold-start generation, finetuning, checkpoint evaluation, or transfer API. "
            "The next step is another dry run to confirm finetuning is now locally reachable.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R157 finetune path patch report.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_patch_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R157 finetune path patch report: "
        f"local_paths={summary['default_paths_are_local']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
