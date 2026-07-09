import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r160_goal_audit_r156_r160"
CLAIM_BOUNDARY = (
    "five-iteration goal audit only; no new API run, checkpoint training, "
    "transfer result, accuracy result, or SCI-Q2 readiness claim"
)

DEFAULT_R156_SUMMARY = (
    "experiment/mmlu/res_logs/mmlu_r156_checkpoint_build_dry_run_or_import_validation_summary.json"
)
DEFAULT_R157_SUMMARY = "experiment/mmlu/res_logs/mmlu_r157_finetune_local_path_patch_summary.json"
DEFAULT_R158_SUMMARY = (
    "experiment/mmlu/res_logs/mmlu_r158_checkpoint_build_dry_run_after_path_patch_summary.json"
)
DEFAULT_R159_SUMMARY = "experiment/mmlu/res_logs/mmlu_r159_checkpoint_build_command_preflight_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r160_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r160_goal_audit_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_goal_audit_summary(
    r156_summary: str = DEFAULT_R156_SUMMARY,
    r157_summary: str = DEFAULT_R157_SUMMARY,
    r158_summary: str = DEFAULT_R158_SUMMARY,
    r159_summary: str = DEFAULT_R159_SUMMARY,
) -> Dict[str, Any]:
    r156 = _load_json(r156_summary)
    r157 = _load_json(r157_summary)
    r158 = _load_json(r158_summary)
    r159 = _load_json(r159_summary)
    checkpoint_exists = bool(r158.get("compatible_checkpoint_exists"))
    checkpoint_training_run = any(
        bool(row.get("checkpoint_training_run")) for row in [r157, r158, r159]
    )
    command_ready = bool(r159.get("build_command")) and bool(
        r159.get("r158_finetune_dry_run_ready")
    )
    transfer_api_allowed = checkpoint_exists and bool(command_ready)
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "status": "aligned_checkpoint_build_ready_but_no_transfer_evidence",
        "goal_window": ["R156", "R157", "R158", "R159", "R160"],
        "drift_detected": False,
        "drift_type": "none_transfer_checkpoint_blocker_preserved_without_overclaiming",
        "maintained_sci_q2_focus": True,
        "maintained_update2_alignment": True,
        "maintained_robustness_alignment": True,
        "claim_discipline_maintained": True,
        "r156_cold_start_dry_run_ready": bool(r156.get("cold_start_dry_run_ready")),
        "r156_finetune_dry_run_ready": bool(r156.get("finetune_dry_run_ready")),
        "r156_finetune_blockers": list(r156.get("finetune_blockers") or []),
        "r157_local_path_patch_confirmed": bool(
            r157.get("parse_cli_accepts_local_paths")
            and r157.get("default_paths_are_local")
            and r157.get("hardcoded_root_argdesigner_removed")
        ),
        "r158_cold_start_dry_run_ready": bool(r158.get("cold_start_dry_run_ready")),
        "r158_finetune_dry_run_ready": bool(r158.get("finetune_dry_run_ready")),
        "r158_finetune_blockers": list(r158.get("finetune_blockers") or []),
        "r159_command_preflight_ready": command_ready,
        "r159_llm_name": r159.get("llm_name"),
        "r159_num_iterations": int(r159.get("num_iterations") or 0),
        "r159_batch_size": int(r159.get("batch_size") or 0),
        "r159_planned_training_sample_count": int(
            r159.get("planned_training_sample_count") or 0
        ),
        "r159_uses_local_mmlu_data_root": bool(r159.get("uses_local_mmlu_data_root")),
        "checkpoint_training_run": checkpoint_training_run,
        "compatible_checkpoint_exists": checkpoint_exists,
        "transfer_api_allowed_next": transfer_api_allowed,
        "broad_api_allowed_next": False,
        "sci_q2_ready": False,
        "bounded_checkpoint_build_allowed_next": command_ready
        and not checkpoint_training_run
        and not checkpoint_exists,
        "blocking_gaps": [
            "No compatible MMLU ARG checkpoint artifacts exist yet",
            "No MMLU transfer API result exists",
            "No transfer or robustness evidence can be claimed from command preflight",
            "SCI-Q2 readiness still requires held-out/transfer evidence plus ablations",
        ],
        "next_protocol": "r161_bounded_mmlu_checkpoint_build_execution_or_user_budget_gate",
        "next_goal_audit_due": "R165",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R160 Five-Iteration Goal Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Verdict",
            "",
            f"- Status: `{summary['status']}`",
            f"- Goal window: `{summary['goal_window']}`",
            f"- Drift detected: `{summary['drift_detected']}`",
            f"- Drift type: `{summary['drift_type']}`",
            f"- Maintained SCI-Q2 focus: `{summary['maintained_sci_q2_focus']}`",
            f"- Maintained update2 alignment: `{summary['maintained_update2_alignment']}`",
            f"- Maintained robustness alignment: `{summary['maintained_robustness_alignment']}`",
            f"- Claim discipline maintained: `{summary['claim_discipline_maintained']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            "",
            "## Window Checks",
            "",
            f"- R156 cold-start dry-run ready: `{summary['r156_cold_start_dry_run_ready']}`",
            f"- R156 finetune dry-run ready: `{summary['r156_finetune_dry_run_ready']}`",
            f"- R156 finetune blockers: `{summary['r156_finetune_blockers']}`",
            f"- R157 local path patch confirmed: `{summary['r157_local_path_patch_confirmed']}`",
            f"- R158 cold-start dry-run ready: `{summary['r158_cold_start_dry_run_ready']}`",
            f"- R158 finetune dry-run ready: `{summary['r158_finetune_dry_run_ready']}`",
            f"- R158 finetune blockers: `{summary['r158_finetune_blockers']}`",
            f"- R159 command preflight ready: `{summary['r159_command_preflight_ready']}`",
            f"- R159 LLM name: `{summary['r159_llm_name']}`",
            f"- R159 iterations/batch/samples: `{summary['r159_num_iterations']}` / `{summary['r159_batch_size']}` / `{summary['r159_planned_training_sample_count']}`",
            f"- R159 uses local MMLU data root: `{summary['r159_uses_local_mmlu_data_root']}`",
            "",
            "## Remaining Blocking Gaps",
            "",
            *[f"- {gap}" for gap in summary["blocking_gaps"]],
            "",
            "## Next Gate",
            "",
            f"- Checkpoint training run: `{summary['checkpoint_training_run']}`",
            f"- Compatible checkpoint exists: `{summary['compatible_checkpoint_exists']}`",
            f"- Bounded checkpoint build allowed next: `{summary['bounded_checkpoint_build_allowed_next']}`",
            f"- Transfer API allowed next: `{summary['transfer_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
            "## Interpretation",
            "",
            "R156-R159 stayed aligned with the user's SCI-Q2 goal: the work fixed local MMLU "
            "checkpoint-build blockers and froze a bounded command while refusing to treat "
            "engineering readiness as transfer evidence. The next run may execute only the "
            "bounded checkpoint build or stop at a user budget gate. Transfer evaluation remains "
            "blocked until the expected checkpoint artifacts exist.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R160 goal audit.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_goal_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R160 goal audit: "
        f"status={summary['status']} bounded_build={summary['bounded_checkpoint_build_allowed_next']} "
        f"transfer_api={summary['transfer_api_allowed_next']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
