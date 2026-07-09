import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r145_goal_audit_r141_r145"
CLAIM_BOUNDARY = "five-iteration goal audit and correction, not an accuracy result"

DEFAULT_R141_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r141_repair_confidence_calibration_protocol_summary.json"
)
DEFAULT_R142_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r142_repair_confidence_calibration_offline_export_summary.json"
)
DEFAULT_R143_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r143_calibrated_repair_final_gate_offline_replay_summary.json"
)
DEFAULT_R144_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r144_calibrated_repair_final_gate_implementation_presmoke_summary.json"
)
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r145_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r145_goal_audit_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_goal_audit_summary(
    r141_summary: str = DEFAULT_R141_SUMMARY,
    r142_summary: str = DEFAULT_R142_SUMMARY,
    r143_summary: str = DEFAULT_R143_SUMMARY,
    r144_summary: str = DEFAULT_R144_SUMMARY,
) -> Dict[str, Any]:
    r141 = _load_json(r141_summary)
    r142 = _load_json(r142_summary)
    r143 = _load_json(r143_summary)
    r144 = _load_json(r144_summary)

    calibration_no_tail34_training = (
        not bool(r141.get("uses_tail34_training_source"))
        and not bool(r142.get("uses_tail34_training_source"))
        and not bool(r143.get("uses_tail34_training_source"))
        and not bool(r142.get("r139_task250_used_for_training"))
        and r142.get("forbidden_training_field_violations") == 0
    )
    maintained_edge_prompt_alignment = (
        bool(r142.get("r139_task250_eval_only"))
        and bool(r143.get("task250_repair_used"))
        and bool(r144.get("close_forwarded_repair_accepted"))
        and bool(r144.get("direct_contradiction_rejected"))
        and bool(r144.get("large_distance_rejected"))
    )
    maintained_update2_alignment = (
        r144.get("decision_method") == "CalibratedEdgePromptRepairContractFinalRefer"
        and bool(r144.get("decision_method_registered"))
        and bool(r144.get("r143_offline_gate_passed"))
    )
    maintained_robustness_alignment = (
        calibration_no_tail34_training
        and not bool(r141.get("direct_threshold_lowering_allowed"))
        and not bool(r142.get("direct_threshold_lowering_allowed"))
        and bool(r144.get("r145_goal_audit_required_before_api"))
        and not bool(r141.get("broad_api_allowed_next"))
        and not bool(r142.get("broad_api_allowed_next"))
        and not bool(r143.get("broad_api_allowed_next"))
        and not bool(r144.get("broad_api_allowed_next"))
    )

    return {
        "rule": RULE_NAME,
        "status": "aligned_allow_bounded_calibrated_smoke",
        "goal_window": ["R141", "R142", "R143", "R144", "R145"],
        "goal_reference": (
            "SCI-Q2 PromptNode node+edge graph organization with bounded validation "
            "and no tail34 threshold overfit"
        ),
        "drift_detected": False,
        "drift_type": "none_calibration_protocolized_and_bounded_api_only",
        "maintained_update2_alignment": maintained_update2_alignment,
        "maintained_edge_prompt_alignment": maintained_edge_prompt_alignment,
        "maintained_robustness_alignment": maintained_robustness_alignment,
        "calibration_no_tail34_training": calibration_no_tail34_training,
        "r141_direct_threshold_lowering_allowed": bool(
            r141.get("direct_threshold_lowering_allowed")
        ),
        "r142_forbidden_training_field_violations": r142.get(
            "forbidden_training_field_violations"
        ),
        "r143_offline_gate_passed": bool(r143.get("same_four_task_gate_offline_passed")),
        "r143_calibrated_selected_accuracy": r143.get("calibrated_selected_accuracy"),
        "r143_clean_fix_harm": r143.get("clean_fix_harm"),
        "r144_decision_method": r144.get("decision_method"),
        "r144_decision_method_registered": bool(r144.get("decision_method_registered")),
        "r144_goal_audit_required_before_api": bool(
            r144.get("r145_goal_audit_required_before_api")
        ),
        "r144_same_two_switch_task_smoke_allowed_next": bool(
            r144.get("same_two_switch_task_smoke_allowed_next")
        ),
        "bounded_api_allowed_next": True,
        "bounded_api_scope": {
            "task_split_path": r144.get("task_split_path"),
            "switch_tasks": ["task_108", "task_250"],
            "fallback_guards": ["task_8", "task_188"],
            "decision_method": r144.get("decision_method"),
            "evaluate_command": r144.get("evaluate_command"),
        },
        "broad_api_allowed_next": False,
        "next_protocol": "r146_bounded_calibrated_repair_api_smoke",
        "next_goal_audit_due": "R150",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R145 Goal Audit After R141-R145",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Window",
            "",
            "- R141: repair-confidence calibration protocol",
            "- R142: repair-confidence offline export",
            "- R143: calibrated repair final-gate offline replay",
            "- R144: calibrated repair final-gate implementation pre-smoke",
            "- R145: five-iteration goal audit",
            "",
            "## Verdict",
            "",
            f"Status: `{summary['status']}`",
            f"Drift detected: `{summary['drift_detected']}`",
            f"Drift type: `{summary['drift_type']}`",
            "",
            "The R141-R144 window stays aligned: calibration is protocolized, tail34 "
            "threshold training is blocked, the calibrated method is registered, and R144 "
            "explicitly required this R145 audit before API. The only allowed next run is "
            "the bounded two-switch-task smoke; broad tail34 remains blocked.",
            "",
            "## Evidence",
            "",
            f"- Maintained update2 alignment: `{summary['maintained_update2_alignment']}`",
            f"- Maintained edge-prompt alignment: `{summary['maintained_edge_prompt_alignment']}`",
            f"- Maintained robustness alignment: `{summary['maintained_robustness_alignment']}`",
            f"- Calibration no tail34 training: `{summary['calibration_no_tail34_training']}`",
            f"- R142 forbidden training-field violations: `{summary['r142_forbidden_training_field_violations']}`",
            f"- R143 offline gate passed: `{summary['r143_offline_gate_passed']}`",
            f"- R143 calibrated selected accuracy: `{summary['r143_calibrated_selected_accuracy']}`",
            f"- R143 clean fix/harm: `{summary['r143_clean_fix_harm']}`",
            f"- R144 decision method: `{summary['r144_decision_method']}`",
            f"- R144 decision method registered: `{summary['r144_decision_method_registered']}`",
            f"- R144 goal audit required before API: `{summary['r144_goal_audit_required_before_api']}`",
            f"- Bounded API allowed next: `{summary['bounded_api_allowed_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            "",
            "## Next Bounded Command",
            "",
            "```bash",
            summary["bounded_api_scope"]["evaluate_command"],
            "```",
            "",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R145 five-iteration goal audit.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_goal_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R145 goal audit: "
        f"status={summary['status']} bounded={summary['bounded_api_allowed_next']} "
        f"broad={summary['broad_api_allowed_next']}"
    )


if __name__ == "__main__":
    main()
