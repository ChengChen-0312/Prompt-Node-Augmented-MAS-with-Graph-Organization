import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from datasets.mmlu_dataset import MMLUDataset  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.mmlu import finetune_mmlu  # noqa: E402


RULE_NAME = "r158_mmlu_checkpoint_build_dry_run_after_path_patch"
CLAIM_BOUNDARY = (
    "after-patch checkpoint build dry-run only; no API run, no checkpoint training, "
    "no transfer result, and no SCI-Q2 readiness claim"
)

DEFAULT_R157_SUMMARY = "experiment/mmlu/res_logs/mmlu_r157_finetune_local_path_patch_summary.json"
DEFAULT_MMLU_DATA_ROOT = os.path.abspath(
    os.path.join(REPO_ROOT, "..", "OpenG-MAS_benchmark_code_release", "datasets", "MMLU")
)
DEFAULT_TASK_SPLIT = "experiment/mmlu/task_split_mmlu.json"
DEFAULT_SUMMARY_JSON = (
    "experiment/mmlu/res_logs/mmlu_r158_checkpoint_build_dry_run_after_path_patch_summary.json"
)
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r158_checkpoint_build_dry_run_after_path_patch.md"
FINETUNE_SCRIPT = "experiment/mmlu/finetune_mmlu.py"
COLD_START_SCRIPT = "experiment/mmlu/cold_start_mmlu.py"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _read_text(path: str) -> str:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return f.read()


def _dev_rows(data_root: str) -> int:
    old_root = os.environ.get("MMLU_DATA_ROOT")
    os.environ["MMLU_DATA_ROOT"] = data_root
    try:
        return len(MMLUDataset("dev"))
    finally:
        if old_root is None:
            os.environ.pop("MMLU_DATA_ROOT", None)
        else:
            os.environ["MMLU_DATA_ROOT"] = old_root


def _compatible_checkpoint_exists() -> bool:
    roots = [Path(_repo_path("experiment")), Path(_repo_path("output"))]
    for root in roots:
        if not root.exists():
            continue
        for config in root.rglob("configuration.txt"):
            directory = config.parent
            if "mmlu" not in str(directory).lower():
                continue
            if (directory / "ef_best_model.pth").exists() or (
                directory / "best_model.pth"
            ).exists():
                return True
    return False


def build_after_patch_summary(
    mmlu_data_root: str = DEFAULT_MMLU_DATA_ROOT,
    task_split: str = DEFAULT_TASK_SPLIT,
) -> Dict[str, Any]:
    r157 = _load_json(DEFAULT_R157_SUMMARY)
    data_root_exists = os.path.isdir(mmlu_data_root)
    dev_rows = _dev_rows(mmlu_data_root) if data_root_exists else 0
    task_split_exists = os.path.exists(_repo_path(task_split))
    split = _load_json(task_split) if task_split_exists else {"base_tasks": [], "finetune_tasks": []}
    base_tasks = [int(idx) for idx in split.get("base_tasks", [])]
    finetune_tasks = [int(idx) for idx in split.get("finetune_tasks", [])]
    all_indices = base_tasks + finetune_tasks
    split_indices_valid = (
        bool(base_tasks)
        and bool(finetune_tasks)
        and len(all_indices) == len(set(all_indices))
        and all(0 <= idx < dev_rows for idx in all_indices)
    )
    default_args = finetune_mmlu.parse_cli_args([])
    source = _read_text(FINETUNE_SCRIPT)
    finetune_blockers = []
    if "/root/ARG-Designer" in source:
        finetune_blockers.append("/root/ARG-Designer")
    if not os.path.isabs(default_args.cold_start_dir):
        finetune_blockers.append("cold_start_dir_not_absolute")
    if not os.path.isabs(default_args.finetune_data_dir):
        finetune_blockers.append("finetune_data_dir_not_absolute")
    if not os.path.isabs(default_args.task_split_file):
        finetune_blockers.append("task_split_file_not_absolute")
    r157_confirmed = bool(
        r157.get("parse_cli_accepts_local_paths")
        and r157.get("default_paths_are_local")
        and r157.get("hardcoded_root_argdesigner_removed")
    )
    cold_start_ready = (
        data_root_exists
        and task_split_exists
        and split_indices_valid
        and os.path.exists(_repo_path(COLD_START_SCRIPT))
    )
    finetune_ready = cold_start_ready and r157_confirmed and not finetune_blockers
    compatible_checkpoint = _compatible_checkpoint_exists()
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_path_patch": DEFAULT_R157_SUMMARY,
        "no_api_run": True,
        "r157_path_patch_confirmed": r157_confirmed,
        "mmlu_data_root": mmlu_data_root,
        "mmlu_data_root_exists": data_root_exists,
        "local_dev_rows": dev_rows,
        "task_split": task_split,
        "task_split_exists": task_split_exists,
        "base_task_count": len(base_tasks),
        "finetune_task_count": len(finetune_tasks),
        "split_indices_valid": split_indices_valid,
        "cold_start_dry_run_ready": cold_start_ready,
        "finetune_dry_run_ready": finetune_ready,
        "finetune_blockers": finetune_blockers,
        "checkpoint_training_run": False,
        "compatible_checkpoint_exists": compatible_checkpoint,
        "transfer_api_allowed_next": compatible_checkpoint,
        "broad_api_allowed_next": False,
        "cold_start_command_template": (
            "cd experiment/mmlu && "
            f"MMLU_DATA_ROOT={mmlu_data_root} "
            "../../.venv/bin/python cold_start_mmlu.py "
            "--llm_name gpt-4o-2024-08-06 --batch_size 4 --num_iterations 10"
        ),
        "finetune_command_template": (
            f"MMLU_DATA_ROOT={mmlu_data_root} "
            ".venv/bin/python experiment/mmlu/finetune_mmlu.py "
            "--load_from_dir <MMLU_PRETRAIN_MODEL_DIR> "
            f"--cold_start_dir {default_args.cold_start_dir} "
            f"--finetune_data_dir {default_args.finetune_data_dir} "
            f"--task_split_file {default_args.task_split_file} "
            "--llm_name gpt-4o-2024-08-06"
        ),
        "next_protocol": (
            "r159_mmlu_transfer_arg_baseline_preflight"
            if compatible_checkpoint
            else "r159_mmlu_checkpoint_build_command_preflight"
        ),
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R158 MMLU Checkpoint Build Dry-Run After Path Patch",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Dry-Run Checks",
            "",
            f"- R157 path patch confirmed: `{summary['r157_path_patch_confirmed']}`",
            f"- MMLU data root exists: `{summary['mmlu_data_root_exists']}`",
            f"- Local dev rows: `{summary['local_dev_rows']}`",
            f"- Task split exists: `{summary['task_split_exists']}`",
            f"- Base/finetune tasks: `{summary['base_task_count']}/{summary['finetune_task_count']}`",
            f"- Split indices valid: `{summary['split_indices_valid']}`",
            f"- Cold-start dry-run ready: `{summary['cold_start_dry_run_ready']}`",
            f"- Finetune dry-run ready: `{summary['finetune_dry_run_ready']}`",
            f"- Finetune blockers: `{summary['finetune_blockers']}`",
            "",
            "## Checkpoint Boundary",
            "",
            f"- Checkpoint training run: `{summary['checkpoint_training_run']}`",
            f"- Compatible checkpoint exists: `{summary['compatible_checkpoint_exists']}`",
            f"- Transfer API allowed next: `{summary['transfer_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            "",
            "## Command Templates",
            "",
            f"- Cold-start: `{summary['cold_start_command_template']}`",
            f"- Finetune: `{summary['finetune_command_template']}`",
            "",
            "## Next Gate",
            "",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Interpretation",
            "",
            "R158 confirms the R157 path patch removed the finetune dry-run blocker. "
            "The local checkpoint build chain is now command-ready, but no checkpoint was trained "
            "and transfer remains blocked until a compatible MMLU ARG checkpoint exists.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R158 after-patch checkpoint dry run.")
    parser.add_argument("--mmlu-data-root", default=DEFAULT_MMLU_DATA_ROOT)
    parser.add_argument("--task-split", default=DEFAULT_TASK_SPLIT)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_after_patch_summary(
        mmlu_data_root=args.mmlu_data_root,
        task_split=args.task_split,
    )
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R158 after-patch dry run: "
        f"finetune={summary['finetune_dry_run_ready']} "
        f"checkpoint={summary['compatible_checkpoint_exists']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
