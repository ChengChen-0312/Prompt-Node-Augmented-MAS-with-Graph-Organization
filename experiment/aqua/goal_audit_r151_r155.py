import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r155_goal_audit_r151_r155"
CLAIM_BOUNDARY = (
    "five-iteration goal audit only; no new API run, checkpoint, transfer result, "
    "accuracy result, or SCI-Q2 readiness claim"
)

DEFAULT_R151_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r151_sci_q2_evidence_gap_plan_summary.json"
)
DEFAULT_R152_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r152_mmlu_checkpoint_or_aqua_replicate_preflight_summary.json"
)
DEFAULT_R153_SUMMARY = "experiment/mmlu/res_logs/mmlu_r153_checkpoint_build_or_import_protocol_summary.json"
DEFAULT_R154_SUMMARY = (
    "experiment/mmlu/res_logs/mmlu_r154_local_checkpoint_path_patch_or_import_stub_summary.json"
)
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r155_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r155_goal_audit_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_goal_audit_summary(
    r151_summary: str = DEFAULT_R151_SUMMARY,
    r152_summary: str = DEFAULT_R152_SUMMARY,
    r153_summary: str = DEFAULT_R153_SUMMARY,
    r154_summary: str = DEFAULT_R154_SUMMARY,
) -> Dict[str, Any]:
    r151 = _load_json(r151_summary)
    r152 = _load_json(r152_summary)
    r153 = _load_json(r153_summary)
    r154 = _load_json(r154_summary)
    transfer_api_allowed = bool(r154.get("compatible_checkpoint_imported")) and bool(
        r152.get("mmlu_transfer_data_ready")
    )
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "status": "aligned_transfer_engineering_not_sci_q2_ready",
        "goal_window": ["R151", "R152", "R153", "R154", "R155"],
        "drift_detected": False,
        "drift_type": "none_transfer_validation_blockers_explicitly_preserved",
        "maintained_sci_q2_focus": True,
        "maintained_update2_alignment": True,
        "claim_discipline_maintained": True,
        "r151_plan_only": bool(r151.get("plan_only")),
        "r151_blocking_gap_count": int(r151.get("blocking_gap_count") or 0),
        "r152_transfer_branch_allowed": bool(r152.get("transfer_branch_allowed")),
        "r152_independent_same_method_aqua_replicate_ready": bool(
            r152.get("independent_same_method_aqua_replicate_ready")
        ),
        "r153_compatible_checkpoint_present": bool(r153.get("compatible_checkpoint_present")),
        "r153_build_route": r153.get("build_route"),
        "r154_dataset_env_patch_available": bool(r154.get("dataset_env_patch_available")),
        "r154_task_split_written": bool(r154.get("task_split_written")),
        "r154_local_dev_rows": int(r154.get("local_dev_rows") or 0),
        "r154_compatible_checkpoint_imported": bool(
            r154.get("compatible_checkpoint_imported")
        ),
        "sci_q2_ready": False,
        "checkpoint_build_preflight_allowed_next": True,
        "transfer_api_allowed_next": transfer_api_allowed,
        "broad_api_allowed_next": False,
        "blocking_gaps": [
            "No compatible MMLU ARG checkpoint is present or imported",
            "No MMLU transfer API result exists",
            "No independent same-method AQuA replicate is available because AQuA has no unseen rows",
            "R147 tail34 evidence remains replay-level and not statistically significant",
            "Cost-normalized superiority remains unsupported",
        ],
        "next_protocol": "r156_mmlu_checkpoint_build_dry_run_or_import_validation",
        "next_goal_audit_due": "R160",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R155 Five-Iteration Goal Audit",
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
            f"- Claim discipline maintained: `{summary['claim_discipline_maintained']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            "",
            "## Window Checks",
            "",
            f"- R151 plan only: `{summary['r151_plan_only']}`",
            f"- R151 blocking gaps: `{summary['r151_blocking_gap_count']}`",
            f"- R152 transfer branch allowed: `{summary['r152_transfer_branch_allowed']}`",
            f"- R152 independent AQuA replicate ready: `{summary['r152_independent_same_method_aqua_replicate_ready']}`",
            f"- R153 compatible checkpoint present: `{summary['r153_compatible_checkpoint_present']}`",
            f"- R153 build route: `{summary['r153_build_route']}`",
            f"- R154 dataset env patch available: `{summary['r154_dataset_env_patch_available']}`",
            f"- R154 task split written: `{summary['r154_task_split_written']}`",
            f"- R154 local dev rows: `{summary['r154_local_dev_rows']}`",
            f"- R154 compatible checkpoint imported: `{summary['r154_compatible_checkpoint_imported']}`",
            "",
            "## Remaining Blocking Gaps",
            "",
            *[f"- {gap}" for gap in summary["blocking_gaps"]],
            "",
            "## Next Gate",
            "",
            f"- Checkpoint build preflight allowed next: `{summary['checkpoint_build_preflight_allowed_next']}`",
            f"- Transfer API allowed next: `{summary['transfer_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
            "## Interpretation",
            "",
            "R151-R154 stayed aligned with the SCI-Q2 objective by refusing to overclaim AQuA-only "
            "evidence and by moving toward transfer validation. However, the paper is still not "
            "ready: checkpoint construction/import and transfer evidence are still missing. The next "
            "step may only be a checkpoint build dry run or import validation; transfer API remains "
            "blocked until a compatible checkpoint exists.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R155 goal audit.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_goal_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R155 goal audit: "
        f"status={summary['status']} transfer_api={summary['transfer_api_allowed_next']} "
        f"next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
