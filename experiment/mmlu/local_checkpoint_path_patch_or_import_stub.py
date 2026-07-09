import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from datasets.mmlu_dataset import MMLUDataset  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r154_local_mmlu_checkpoint_path_patch_or_import_stub"
CLAIM_BOUNDARY = (
    "local dataset path patch and checkpoint import stub only; no API run, "
    "no checkpoint training, no transfer result, and no SCI-Q2 readiness claim"
)

DEFAULT_R153_SUMMARY = "experiment/mmlu/res_logs/mmlu_r153_checkpoint_build_or_import_protocol_summary.json"
DEFAULT_LOCAL_MMLU_ROOT = os.path.abspath(
    os.path.join(REPO_ROOT, "..", "OpenG-MAS_benchmark_code_release", "datasets", "MMLU")
)
DEFAULT_TASK_SPLIT_JSON = "experiment/mmlu/task_split_mmlu.json"
DEFAULT_SUMMARY_JSON = (
    "experiment/mmlu/res_logs/mmlu_r154_local_checkpoint_path_patch_or_import_stub_summary.json"
)
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r154_local_checkpoint_path_patch_or_import_stub.md"

DEFAULT_TRAIN_SAMPLE_COUNT = 40
DEFAULT_BASE_RATE = 0.4
DEFAULT_SEED = 42


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _with_mmlu_root(data_root: str) -> int:
    old_root = os.environ.get("MMLU_DATA_ROOT")
    os.environ["MMLU_DATA_ROOT"] = data_root
    try:
        dataset = MMLUDataset("dev")
        return len(dataset)
    finally:
        if old_root is None:
            os.environ.pop("MMLU_DATA_ROOT", None)
        else:
            os.environ["MMLU_DATA_ROOT"] = old_root


def _planned_split(
    total_rows: int,
    train_sample_count: int = DEFAULT_TRAIN_SAMPLE_COUNT,
    base_rate: float = DEFAULT_BASE_RATE,
    seed: int = DEFAULT_SEED,
) -> Dict[str, List[int]]:
    train_count = min(train_sample_count, total_rows)
    candidates = list(range(train_count))
    rng = random.Random(seed)
    rng.shuffle(candidates)
    base_count = int(base_rate * len(candidates))
    return {
        "base_tasks": candidates[:base_count],
        "finetune_tasks": candidates[base_count:],
    }


def _checkpoint_import_valid(checkpoint_dir: Optional[str]) -> bool:
    if not checkpoint_dir:
        return False
    path = Path(_repo_path(checkpoint_dir))
    if not path.exists() or not path.is_dir():
        return False
    has_config = (path / "configuration.txt").exists()
    has_weight = (path / "ef_best_model.pth").exists() or (path / "best_model.pth").exists()
    return has_config and has_weight


def _write_split(path: str, data: Dict[str, Any]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def build_local_patch_summary(
    write_split: bool = True,
    mmlu_data_root: str = DEFAULT_LOCAL_MMLU_ROOT,
    task_split_json: str = DEFAULT_TASK_SPLIT_JSON,
    checkpoint_dir: Optional[str] = None,
) -> Dict[str, Any]:
    local_root_exists = os.path.isdir(mmlu_data_root)
    local_dev_rows = _with_mmlu_root(mmlu_data_root) if local_root_exists else 0
    split = _planned_split(local_dev_rows)
    split_payload = {
        **split,
        "source": RULE_NAME,
        "mmlu_data_root": mmlu_data_root,
        "dev_rows": local_dev_rows,
        "train_sample_count": min(DEFAULT_TRAIN_SAMPLE_COUNT, local_dev_rows),
        "base_rate": DEFAULT_BASE_RATE,
        "seed": DEFAULT_SEED,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if write_split:
        _write_split(task_split_json, split_payload)

    compatible_import = _checkpoint_import_valid(checkpoint_dir)
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_protocol": DEFAULT_R153_SUMMARY,
        "no_api_run": True,
        "dataset_env_patch_available": True,
        "local_mmlu_root": mmlu_data_root,
        "local_mmlu_root_exists": local_root_exists,
        "local_dev_rows": local_dev_rows,
        "task_split_json": task_split_json,
        "task_split_written": bool(write_split),
        "planned_base_task_count": len(split["base_tasks"]),
        "planned_finetune_task_count": len(split["finetune_tasks"]),
        "planned_train_sample_count": len(split["base_tasks"]) + len(split["finetune_tasks"]),
        "split_seed": DEFAULT_SEED,
        "import_stub_available": True,
        "checkpoint_dir_checked": checkpoint_dir or "",
        "compatible_checkpoint_imported": compatible_import,
        "transfer_api_allowed_next": False,
        "broad_api_allowed_next": False,
        "next_protocol": "r155_goal_audit_r151_r155",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R154 Local MMLU Checkpoint Path Patch or Import Stub",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Local Dataset Path",
            "",
            f"- Dataset env patch available: `{summary['dataset_env_patch_available']}`",
            f"- Local MMLU root: `{summary['local_mmlu_root']}`",
            f"- Local MMLU root exists: `{summary['local_mmlu_root_exists']}`",
            f"- Local dev rows: `{summary['local_dev_rows']}`",
            "",
            "## Task Split",
            "",
            f"- Task split JSON: `{summary['task_split_json']}`",
            f"- Task split written: `{summary['task_split_written']}`",
            f"- Planned base tasks: `{summary['planned_base_task_count']}`",
            f"- Planned finetune tasks: `{summary['planned_finetune_task_count']}`",
            f"- Split seed: `{summary['split_seed']}`",
            "",
            "## Checkpoint Import Stub",
            "",
            f"- Import stub available: `{summary['import_stub_available']}`",
            f"- Checkpoint dir checked: `{summary['checkpoint_dir_checked']}`",
            f"- Compatible checkpoint imported: `{summary['compatible_checkpoint_imported']}`",
            "",
            "## Next Gate",
            "",
            f"- Transfer API allowed next: `{summary['transfer_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Interpretation",
            "",
            "R154 makes local MMLU data visible through `MMLU_DATA_ROOT` and writes a deterministic "
            "base/finetune task split for the existing cold-start/finetune pipeline. It does not train "
            "a checkpoint or authorize transfer API; R155 must audit the R151-R155 window before any "
            "costly run.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R154 local MMLU path/import stub.")
    parser.add_argument("--mmlu-data-root", default=DEFAULT_LOCAL_MMLU_ROOT)
    parser.add_argument("--task-split-json", default=DEFAULT_TASK_SPLIT_JSON)
    parser.add_argument("--checkpoint-dir", default=None)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_local_patch_summary(
        write_split=True,
        mmlu_data_root=args.mmlu_data_root,
        task_split_json=args.task_split_json,
        checkpoint_dir=args.checkpoint_dir,
    )
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R154 local MMLU path/import stub: "
        f"dev_rows={summary['local_dev_rows']} split={summary['task_split_written']} "
        f"checkpoint={summary['compatible_checkpoint_imported']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
