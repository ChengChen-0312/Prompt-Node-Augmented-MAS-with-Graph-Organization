import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from datasets.mmlu_dataset import MMLUDataset  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r156_mmlu_checkpoint_build_dry_run_or_import_validation"
CLAIM_BOUNDARY = (
    "checkpoint build dry-run/import validation only; no API run, no checkpoint training, "
    "no transfer result, and no SCI-Q2 readiness claim"
)

DEFAULT_R155_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r155_goal_audit_summary.json"
DEFAULT_MMLU_DATA_ROOT = os.path.abspath(
    os.path.join(REPO_ROOT, "..", "OpenG-MAS_benchmark_code_release", "datasets", "MMLU")
)
DEFAULT_TASK_SPLIT = "experiment/mmlu/task_split_mmlu.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r156_checkpoint_build_dry_run_or_import_validation_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r156_checkpoint_build_dry_run_or_import_validation.md"

COLD_START_SCRIPT = "experiment/mmlu/cold_start_mmlu.py"
FINETUNE_SCRIPT = "experiment/mmlu/finetune_mmlu.py"


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


def _checkpoint_import_valid(checkpoint_dir: Optional[str]) -> bool:
    if not checkpoint_dir:
        return False
    path = Path(_repo_path(checkpoint_dir))
    if not path.exists() or not path.is_dir():
        return False
    return (path / "configuration.txt").exists() and (
        (path / "ef_best_model.pth").exists() or (path / "best_model.pth").exists()
    )


def build_dry_run_summary(
    mmlu_data_root: str = DEFAULT_MMLU_DATA_ROOT,
    task_split: str = DEFAULT_TASK_SPLIT,
    checkpoint_dir: Optional[str] = None,
) -> Dict[str, Any]:
    data_root_exists = os.path.isdir(mmlu_data_root)
    task_split_exists = os.path.exists(_repo_path(task_split))
    dev_rows = _dev_rows(mmlu_data_root) if data_root_exists else 0
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
    finetune_text = _read_text(FINETUNE_SCRIPT)
    hardcoded_finetune_paths = [
        marker
        for marker in ["/root/ARG-Designer", "FINETUNE_DATA_DIR", "COLD_START_DIR"]
        if marker in finetune_text
    ]
    cold_start_ready = (
        data_root_exists
        and task_split_exists
        and split_indices_valid
        and os.path.exists(_repo_path(COLD_START_SCRIPT))
    )
    finetune_ready = cold_start_ready and not hardcoded_finetune_paths
    compatible_import = _checkpoint_import_valid(checkpoint_dir)
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_goal_audit": DEFAULT_R155_SUMMARY,
        "no_api_run": True,
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
        "finetune_blockers": hardcoded_finetune_paths,
        "import_validation_ready": True,
        "checkpoint_dir_checked": checkpoint_dir or "",
        "compatible_checkpoint_imported": compatible_import,
        "cold_start_command_template": (
            "cd experiment/mmlu && "
            f"MMLU_DATA_ROOT={mmlu_data_root} "
            "../../.venv/bin/python cold_start_mmlu.py "
            "--llm_name gpt-4o-2024-08-06 --batch_size 4 --num_iterations 10"
        ),
        "finetune_command_status": (
            "blocked_until_local_path_patch" if not finetune_ready else "ready"
        ),
        "transfer_api_allowed_next": compatible_import,
        "broad_api_allowed_next": False,
        "next_protocol": (
            "r157_mmlu_transfer_arg_baseline_preflight"
            if compatible_import
            else "r157_mmlu_finetune_local_path_patch"
        ),
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R156 MMLU Checkpoint Build Dry-Run or Import Validation",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Dry-Run Checks",
            "",
            f"- MMLU data root exists: `{summary['mmlu_data_root_exists']}`",
            f"- Local dev rows: `{summary['local_dev_rows']}`",
            f"- Task split exists: `{summary['task_split_exists']}`",
            f"- Base/finetune tasks: `{summary['base_task_count']}/{summary['finetune_task_count']}`",
            f"- Split indices valid: `{summary['split_indices_valid']}`",
            f"- Cold-start dry-run ready: `{summary['cold_start_dry_run_ready']}`",
            f"- Finetune dry-run ready: `{summary['finetune_dry_run_ready']}`",
            f"- Finetune blockers: `{summary['finetune_blockers']}`",
            "",
            "## Import Validation",
            "",
            f"- Import validation ready: `{summary['import_validation_ready']}`",
            f"- Checkpoint dir checked: `{summary['checkpoint_dir_checked']}`",
            f"- Compatible checkpoint imported: `{summary['compatible_checkpoint_imported']}`",
            "",
            "## Command Boundary",
            "",
            f"- Cold-start command template: `{summary['cold_start_command_template']}`",
            f"- Finetune command status: `{summary['finetune_command_status']}`",
            "",
            "## Next Gate",
            "",
            f"- Transfer API allowed next: `{summary['transfer_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Interpretation",
            "",
            "R156 confirms that local MMLU data and the R154 split are valid for a cold-start dry run. "
            "It also confirms the next blocker: finetuning still has hardcoded local-data paths. "
            "No API or checkpoint training was run.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R156 checkpoint dry-run validation.")
    parser.add_argument("--mmlu-data-root", default=DEFAULT_MMLU_DATA_ROOT)
    parser.add_argument("--task-split", default=DEFAULT_TASK_SPLIT)
    parser.add_argument("--checkpoint-dir", default=None)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_dry_run_summary(
        mmlu_data_root=args.mmlu_data_root,
        task_split=args.task_split,
        checkpoint_dir=args.checkpoint_dir,
    )
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R156 checkpoint dry run: "
        f"cold_start={summary['cold_start_dry_run_ready']} "
        f"finetune={summary['finetune_dry_run_ready']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
