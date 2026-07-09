import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r159_mmlu_checkpoint_build_command_preflight"
CLAIM_BOUNDARY = (
    "checkpoint build command preflight only; no API run, no checkpoint training, "
    "no transfer result, and no SCI-Q2 readiness claim"
)

DEFAULT_R158_SUMMARY = (
    "experiment/mmlu/res_logs/mmlu_r158_checkpoint_build_dry_run_after_path_patch_summary.json"
)
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r159_checkpoint_build_command_preflight_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r159_checkpoint_build_command_preflight.md"

LLM_NAME = "gpt-4o-2024-08-06"
NUM_ITERATIONS = 10
BATCH_SIZE = 4
MODEL_OUTPUT_DIR = "experiment/mmlu/output/mmlu_arg_base_model_r159"
FINETUNE_DATA_DIR = "experiment/FinetuneData_mmlu"
COLD_START_DIR = "experiment/ColdStartData_mmlu"
TASK_SPLIT_FILE = "experiment/mmlu/task_split_mmlu.json"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _abs(path: str) -> str:
    return _repo_path(path)


def _build_command(mmlu_data_root: str) -> str:
    return " ".join(
        [
            f"MMLU_DATA_ROOT={mmlu_data_root}",
            ".venv/bin/python experiment/mmlu/finetune_mmlu.py",
            "--pretrain",
            f"--llm_name {LLM_NAME}",
            f"--num_iterations {NUM_ITERATIONS}",
            f"--batch_size {BATCH_SIZE}",
            f"--model_output_dir {_abs(MODEL_OUTPUT_DIR)}",
            "--no_timestamp_output_dir",
            f"--cold_start_dir {_abs(COLD_START_DIR)}",
            f"--finetune_data_dir {_abs(FINETUNE_DATA_DIR)}",
            f"--task_split_file {_abs(TASK_SPLIT_FILE)}",
        ]
    )


def build_command_preflight_summary() -> Dict[str, Any]:
    r158 = _load_json(DEFAULT_R158_SUMMARY)
    planned_count = int(r158.get("base_task_count") or 0) + int(
        r158.get("finetune_task_count") or 0
    )
    mmlu_data_root = str(r158.get("mmlu_data_root") or "")
    expected_artifacts = [
        os.path.join(_abs(MODEL_OUTPUT_DIR), "configuration.txt"),
        os.path.join(_abs(MODEL_OUTPUT_DIR), "best_model.pth"),
        os.path.join(_abs(MODEL_OUTPUT_DIR), "ef_best_model.pth"),
    ]
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_dry_run": DEFAULT_R158_SUMMARY,
        "no_api_run": True,
        "r158_finetune_dry_run_ready": bool(r158.get("finetune_dry_run_ready")),
        "llm_name": LLM_NAME,
        "num_iterations": NUM_ITERATIONS,
        "batch_size": BATCH_SIZE,
        "planned_training_sample_count": planned_count,
        "uses_local_mmlu_data_root": bool(
            mmlu_data_root and os.path.isdir(mmlu_data_root)
        ),
        "mmlu_data_root": mmlu_data_root,
        "model_output_dir": _abs(MODEL_OUTPUT_DIR),
        "cold_start_dir": _abs(COLD_START_DIR),
        "finetune_data_dir": _abs(FINETUNE_DATA_DIR),
        "task_split_file": _abs(TASK_SPLIT_FILE),
        "build_command": _build_command(mmlu_data_root),
        "expected_checkpoint_artifacts": expected_artifacts,
        "success_gate": "configuration.txt plus best_model.pth and ef_best_model.pth exist",
        "stop_conditions": [
            "API quota or authentication failure",
            "MMLU dev data root unavailable",
            "task split invalid",
            "pretrain or finetune loss becomes NaN",
            "expected checkpoint artifacts missing after run",
        ],
        "checkpoint_training_run": False,
        "transfer_api_allowed_next": False,
        "broad_api_allowed_next": False,
        "next_protocol": "r160_goal_audit_r156_r160",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R159 MMLU Checkpoint Build Command Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Command",
            "",
            f"```bash\n{summary['build_command']}\n```",
            "",
            "## Bounded Run Settings",
            "",
            f"- No API run: `{summary['no_api_run']}`",
            f"- R158 finetune dry-run ready: `{summary['r158_finetune_dry_run_ready']}`",
            f"- LLM name: `{summary['llm_name']}`",
            f"- Num iterations: `{summary['num_iterations']}`",
            f"- Batch size: `{summary['batch_size']}`",
            f"- Planned training sample count: `{summary['planned_training_sample_count']}`",
            f"- Uses local MMLU data root: `{summary['uses_local_mmlu_data_root']}`",
            "",
            "## Expected Artifacts",
            "",
            *[f"- `{artifact}`" for artifact in summary["expected_checkpoint_artifacts"]],
            "",
            "## Stop Conditions",
            "",
            *[f"- {condition}" for condition in summary["stop_conditions"]],
            "",
            "## Next Gate",
            "",
            f"- Checkpoint training run: `{summary['checkpoint_training_run']}`",
            f"- Transfer API allowed next: `{summary['transfer_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Interpretation",
            "",
            "R159 defines the exact bounded command for building a compatible MMLU ARG checkpoint. "
            "It intentionally does not run the command. R160 must audit the R156-R160 window before "
            "any API-backed checkpoint build proceeds.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R159 checkpoint command preflight.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_command_preflight_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R159 checkpoint command preflight: "
        f"samples={summary['planned_training_sample_count']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
