from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict

import torch


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_ARG_CHECKPOINT_DIR = "experiment/mmlu/output/mmlu_arg_base_model_r159"
DEFAULT_PN_CHECKPOINT_DIR = "experiment/mmlu/output/mmlu_promptedge_pn_graph_policy_r188_e5"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r281_training_protocol_freeze_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r281_training_protocol_freeze.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _checkpoint_state(path: str, expected_pn: bool) -> Dict[str, Any]:
    root = _repo_path(path)
    cfg = _load_json(root / "configuration.txt")
    role_mapping = cfg.get("role_mapping", {}) if isinstance(cfg, dict) else {}
    pn_roles = sorted(role for role in role_mapping if str(role).startswith("PN_"))
    weight_paths = [
        root / "best_model.pth",
        root / "ef_best_model.pth",
    ]
    return {
        "path": path,
        "checkpoint_exists": root.exists() and any(p.exists() for p in weight_paths) and bool(cfg),
        "configuration_exists": (root / "configuration.txt").exists(),
        "best_model_exists": (root / "best_model.pth").exists(),
        "ef_best_model_exists": (root / "ef_best_model.pth").exists(),
        "role_mapping_size": len(role_mapping),
        "role_mapping_keys": sorted(role_mapping.keys()),
        "pn_roles_present": pn_roles,
        "expected_pn_roles": expected_pn,
        "role_mapping_compatible_with_promptnodes": bool(pn_roles) if expected_pn else not bool(pn_roles),
        "epochs": cfg.get("epochs"),
        "batch_size": cfg.get("batch_size"),
        "device": cfg.get("device"),
    }


def _path_exists(path: str) -> bool:
    return _repo_path(path).exists()


def build_r281_protocol_summary(
    arg_checkpoint_dir: str = DEFAULT_ARG_CHECKPOINT_DIR,
    promptnode_checkpoint_dir: str = DEFAULT_PN_CHECKPOINT_DIR,
) -> Dict[str, Any]:
    arg_state = _checkpoint_state(arg_checkpoint_dir, expected_pn=False)
    pn_state = _checkpoint_state(promptnode_checkpoint_dir, expected_pn=True)
    mps_available = bool(hasattr(torch.backends, "mps") and torch.backends.mps.is_available())
    splits = {
        "tiny16_probe_exists": _path_exists("experiment/mmlu/run_logs/mmlu_r251_mmlu_transfer_probe_tiny16.jsonl"),
        "full24_probe_exists": _path_exists("experiment/mmlu/run_logs/mmlu_r251_mmlu_transfer_probe_full24.jsonl"),
        "transfer100_exists": _path_exists("experiment/mmlu/task_split_mmlu_stem_transfer100.json"),
        "mmlu_task_split_exists": _path_exists("experiment/mmlu/task_split_mmlu.json"),
        "transfer_eval_results_exists": _path_exists("experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl"),
    }
    scripts = {
        "finetune_mmlu_exists": _path_exists("experiment/mmlu/finetune_mmlu.py"),
        "train_argdesigner_exists": _path_exists("experiment/train_ARGDesigner.py"),
        "evaluate_mmlu_exists": _path_exists("experiment/mmlu/evaluate_mmlu.py"),
        "promptedge_training_dry_run_exists": _path_exists("experiment/mmlu/r184_promptedge_training_dry_run.py"),
    }
    training_authorized = (
        arg_state["checkpoint_exists"]
        and pn_state["checkpoint_exists"]
        and arg_state["role_mapping_compatible_with_promptnodes"]
        and pn_state["role_mapping_compatible_with_promptnodes"]
        and splits["full24_probe_exists"]
        and splits["transfer100_exists"]
        and scripts["finetune_mmlu_exists"]
    )
    return {
        "run_id": "R281",
        "title": "MMLU ARG vs PromptNode retrain protocol freeze",
        "claim_boundary": "Protocol freeze only; no training launched, no API call, no transfer superiority claim, and no SCI-Q2 readiness claim.",
        "no_api": True,
        "broad_api": False,
        "platform": platform.platform(),
        "torch_version": torch.__version__,
        "mps_available": mps_available,
        "cuda_available": bool(torch.cuda.is_available()),
        "arg_training_path": arg_state,
        "promptnode_training_path": pn_state,
        "splits": splits,
        "scripts": scripts,
        "fairness_requirements": [
            "same held-out full24 and transfer100 evaluation items",
            "same evaluation LLM gpt-4o-2024-08-06",
            "same decision method FinalRefer",
            "PromptNode roles must be present in training graph data before checkpoint training",
            "old ARG checkpoint cannot be directly finetuned into PN role mapping",
            "plain requery remains a strong control and must be reported",
        ],
        "claim_permissions": {
            "training_launch_allowed": training_authorized,
            "api_evaluation_allowed": False,
            "transfer_superiority_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "training_authorized_next": training_authorized,
        "next_runs": ["R282_ARG_retrain", "R283_PromptNode_retrain"],
        "next_goal_audit_due": "R285",
    }


def render_report(summary: Dict[str, Any]) -> str:
    arg = summary["arg_training_path"]
    pn = summary["promptnode_training_path"]
    return "\n".join(
        [
            "# R281 MMLU ARG vs PromptNode Retrain Protocol Freeze",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Environment",
            "",
            f"- Platform: `{summary['platform']}`",
            f"- Torch: `{summary['torch_version']}`",
            f"- MPS available: `{summary['mps_available']}`",
            f"- CUDA available: `{summary['cuda_available']}`",
            "",
            "## Checkpoints",
            "",
            f"- ARG checkpoint: `{arg['path']}`; exists `{arg['checkpoint_exists']}`; role mapping `{arg['role_mapping_size']}`",
            f"- PromptNode checkpoint: `{pn['path']}`; exists `{pn['checkpoint_exists']}`; role mapping `{pn['role_mapping_size']}`; PN roles `{pn['pn_roles_present']}`",
            "",
            "## Splits",
            "",
            *[f"- {key}: `{value}`" for key, value in summary["splits"].items()],
            "",
            "## Fairness Requirements",
            "",
            *[f"- {item}" for item in summary["fairness_requirements"]],
            "",
            "## Permissions",
            "",
            f"- Training authorized next: `{summary['training_authorized_next']}`",
            f"- API evaluation allowed now: `{summary['claim_permissions']['api_evaluation_allowed']}`",
            f"- Transfer superiority claim allowed: `{summary['claim_permissions']['transfer_superiority_claim_allowed']}`",
            f"- Next runs: `{summary['next_runs']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
        ]
    )


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    arg_checkpoint_dir: str = DEFAULT_ARG_CHECKPOINT_DIR,
    promptnode_checkpoint_dir: str = DEFAULT_PN_CHECKPOINT_DIR,
) -> Dict[str, Any]:
    summary = build_r281_protocol_summary(arg_checkpoint_dir, promptnode_checkpoint_dir)
    summary_path = _repo_path(summary_json)
    report_path = _repo_path(report_md)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze R281 MMLU retrain protocol.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--arg_checkpoint_dir", default=DEFAULT_ARG_CHECKPOINT_DIR)
    parser.add_argument("--promptnode_checkpoint_dir", default=DEFAULT_PN_CHECKPOINT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
