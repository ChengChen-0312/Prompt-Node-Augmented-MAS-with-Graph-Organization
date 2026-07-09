import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r153_mmlu_checkpoint_build_or_import_protocol"
CLAIM_BOUNDARY = (
    "checkpoint build/import protocol only; no API run, no checkpoint produced, "
    "no transfer result, and no SCI-Q2 readiness claim"
)

DEFAULT_R152_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r152_mmlu_checkpoint_or_aqua_replicate_preflight_summary.json"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/mmlu/res_logs/mmlu_r153_checkpoint_build_or_import_protocol_summary.json"
)
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r153_checkpoint_build_or_import_protocol.md"

FINETUNE_SCRIPT = "experiment/mmlu/finetune_mmlu.py"
COLD_START_SCRIPT = "experiment/mmlu/cold_start_mmlu.py"
EVALUATOR_SCRIPT = "experiment/mmlu/evaluate_mmlu.py"
LOCAL_TASK_SPLIT_CANDIDATES = [
    "task_split_mmlu.json",
    "experiment/mmlu/task_split_mmlu.json",
]
CHECKPOINT_SUFFIXES = {".pt", ".pth", ".ckpt", ".pkl"}


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _read_text(path: str) -> str:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return f.read()


def _mmlu_checkpoint_dirs() -> List[str]:
    roots = [Path(_repo_path("experiment")), Path(_repo_path("output"))]
    dirs = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in CHECKPOINT_SUFFIXES:
                continue
            lower_path = str(path).lower()
            if "mmlu" in lower_path:
                dirs.add(os.path.relpath(path.parent, REPO_ROOT))
    compatible = []
    for directory in sorted(dirs):
        abs_dir = Path(_repo_path(directory))
        has_config = (abs_dir / "configuration.txt").exists()
        has_weight = (abs_dir / "ef_best_model.pth").exists() or (abs_dir / "best_model.pth").exists()
        if has_config and has_weight:
            compatible.append(directory)
    return compatible


def build_checkpoint_protocol_summary() -> Dict[str, Any]:
    finetune_text = _read_text(FINETUNE_SCRIPT)
    cold_start_text = _read_text(COLD_START_SCRIPT)
    compatible_dirs = _mmlu_checkpoint_dirs()
    hardcoded_roots = [
        marker
        for marker in ["/root/ARG-Designer", "../ColdStartData_mmlu", "./task_split_mmlu.json"]
        if marker in finetune_text or marker in cold_start_text
    ]
    local_task_split_exists = any(os.path.exists(_repo_path(path)) for path in LOCAL_TASK_SPLIT_CANDIDATES)

    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_preflight": DEFAULT_R152_SUMMARY,
        "no_api_run": True,
        "compatible_checkpoint_present": bool(compatible_dirs),
        "compatible_checkpoint_dirs": compatible_dirs,
        "mmlu_finetune_script_exists": os.path.exists(_repo_path(FINETUNE_SCRIPT)),
        "mmlu_cold_start_script_exists": os.path.exists(_repo_path(COLD_START_SCRIPT)),
        "mmlu_evaluator_exists": os.path.exists(_repo_path(EVALUATOR_SCRIPT)),
        "hardcoded_root_paths_detected": bool(hardcoded_roots),
        "hardcoded_path_markers": hardcoded_roots,
        "local_task_split_exists": local_task_split_exists,
        "local_task_split_candidates": LOCAL_TASK_SPLIT_CANDIDATES,
        "import_route_supported": True,
        "required_import_files": [
            "configuration.txt",
            "ef_best_model.pth or best_model.pth",
        ],
        "build_route": (
            "use_imported_checkpoint"
            if compatible_dirs
            else "patch_local_paths_then_coldstart_pretrain_finetune"
        ),
        "build_route_required_steps": [
            "replace hardcoded /root paths with CLI-configurable local paths",
            "generate or provide task_split_mmlu.json for dev base/finetune split",
            "run cold_start_mmlu.py with gpt-4o-2024-08-06 only after API budget is approved",
            "run finetune_mmlu.py with local data dirs and model output dir",
            "verify configuration.txt plus ef_best_model.pth before transfer evaluation",
        ],
        "transfer_api_allowed_next": False,
        "broad_api_allowed_next": False,
        "next_protocol": "r154_local_mmlu_checkpoint_path_patch_or_import_stub",
        "next_goal_audit_due": "R155",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R153 MMLU Checkpoint Build or Import Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Current Checkpoint State",
            "",
            f"- Compatible checkpoint present: `{summary['compatible_checkpoint_present']}`",
            f"- Compatible checkpoint dirs: `{summary['compatible_checkpoint_dirs']}`",
            f"- Finetune script exists: `{summary['mmlu_finetune_script_exists']}`",
            f"- Cold-start script exists: `{summary['mmlu_cold_start_script_exists']}`",
            f"- Evaluator exists: `{summary['mmlu_evaluator_exists']}`",
            f"- Hardcoded path markers: `{summary['hardcoded_path_markers']}`",
            f"- Local task split exists: `{summary['local_task_split_exists']}`",
            "",
            "## Build or Import Route",
            "",
            f"- Import route supported: `{summary['import_route_supported']}`",
            f"- Required import files: `{summary['required_import_files']}`",
            f"- Build route: `{summary['build_route']}`",
            "",
            "## Required Steps",
            "",
            *[f"- {step}" for step in summary["build_route_required_steps"]],
            "",
            "## Next Gate",
            "",
            f"- Transfer API allowed next: `{summary['transfer_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
            "## Interpretation",
            "",
            "R153 keeps transfer validation blocked until a compatible MMLU ARG checkpoint exists. "
            "The existing MMLU scripts are useful, but the finetune/cold-start path still needs local "
            "path configurability and a task split manifest before a checkpoint can be built in this workspace.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R153 MMLU checkpoint protocol.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_checkpoint_protocol_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R153 checkpoint protocol: "
        f"checkpoint={summary['compatible_checkpoint_present']} "
        f"route={summary['build_route']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
