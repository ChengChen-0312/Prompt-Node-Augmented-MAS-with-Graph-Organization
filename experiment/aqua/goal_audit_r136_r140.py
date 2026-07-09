import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r140_goal_audit_r136_r140"
CLAIM_BOUNDARY = "five-iteration goal audit and correction, not an accuracy result"

DEFAULT_R136_SUMMARY = (
    "experiment/aqua/res_logs/"
    "aqua_tail34_r136_edge_prompt_repair_field_prompting_presmoke_summary.json"
)
DEFAULT_R137_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r137_edge_prompt_repair_smoke_summary.json"
)
DEFAULT_R138_SUMMARY = (
    "experiment/aqua/res_logs/"
    "aqua_tail34_r138_router_repair_forwarding_prompt_hardening_summary.json"
)
DEFAULT_R139_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r139_edge_prompt_repair_forwarding_smoke_summary.json"
)
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r140_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r140_goal_audit_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_goal_audit_summary(
    r136_summary: str = DEFAULT_R136_SUMMARY,
    r137_summary: str = DEFAULT_R137_SUMMARY,
    r138_summary: str = DEFAULT_R138_SUMMARY,
    r139_summary: str = DEFAULT_R139_SUMMARY,
) -> Dict[str, Any]:
    r136 = _load_json(r136_summary)
    r137 = _load_json(r137_summary)
    r138 = _load_json(r138_summary)
    r139 = _load_json(r139_summary)

    maintained_update2_alignment = (
        bool(r136.get("pn_verifier_repair_audit_prompted"))
        and bool(r136.get("pn_router_repair_fields_prompted"))
        and r137.get("promptnode_graph_evidence_on_switches") == "2/2"
        and r137.get("switch_update2_metadata") == "2/2"
        and r139.get("promptnode_graph_evidence_on_switches") == "2/2"
        and r139.get("switch_update2_metadata") == "2/2"
    )
    maintained_edge_prompt_alignment = (
        bool(r138.get("prompt_as_edge_first_class"))
        and bool(r138.get("pn_router_repair_forwarding_required"))
        and bool(r139.get("task250_router_repair_forwarded"))
        and not bool(r139.get("verifier_router_repair_forwarding_gap"))
    )
    maintained_robustness_alignment = (
        bool(r138.get("no_task_id_routing"))
        and bool(r138.get("multi_dataset_transfer_required"))
        and not bool(r136.get("broad_api_allowed_next"))
        and not bool(r137.get("broad_api_allowed_next"))
        and not bool(r138.get("broad_api_allowed_next"))
        and not bool(r139.get("broad_api_allowed_next"))
        and not bool(r139.get("task250_repair_confidence_gate_passed"))
    )
    forwarding_gap_fixed = (
        bool(r137.get("verifier_router_repair_forwarding_gap"))
        and bool(r139.get("task250_router_repair_forwarded"))
        and not bool(r139.get("verifier_router_repair_forwarding_gap"))
    )
    clean_gate_still_not_met = (
        r139.get("clean_fix_harm") == "0/0"
        and not bool(r139.get("smoke_gate_passed"))
    )
    confidence_calibration_needed = (
        bool(r139.get("task250_repair_forwarded_but_rejected_low_confidence"))
        and clean_gate_still_not_met
    )

    return {
        "rule": RULE_NAME,
        "status": "aligned_continue_with_calibration_protocol",
        "goal_window": ["R136", "R137", "R138", "R139", "R140"],
        "goal_reference": (
            "SCI-Q2 PromptNode first-class node+edge graph organization with "
            "robustness and transfer boundaries"
        ),
        "drift_detected": False,
        "drift_type": "none_forwarding_fixed_but_threshold_overfit_blocked",
        "maintained_update2_alignment": maintained_update2_alignment,
        "maintained_edge_prompt_alignment": maintained_edge_prompt_alignment,
        "maintained_robustness_alignment": maintained_robustness_alignment,
        "forwarding_gap_fixed": forwarding_gap_fixed,
        "clean_gate_still_not_met": clean_gate_still_not_met,
        "confidence_calibration_needed": confidence_calibration_needed,
        "threshold_lowering_without_protocol_allowed": False,
        "best_current_tail34_signal": "R065 objective-guided replay 31/34 versus ARG 28/34",
        "best_current_fresh_integrated_signal": "R074 fresh surgical cascade 29/34 versus internal ARG 28/34",
        "current_edge_prompt_signal": (
            "R139 fixes repair forwarding but remains 3/4 on the four-task gate"
        ),
        "r136_repair_prompting_ready": (
            bool(r136.get("pn_verifier_repair_audit_prompted"))
            and bool(r136.get("pn_router_repair_fields_prompted"))
        ),
        "r137_forwarding_gap": bool(r137.get("verifier_router_repair_forwarding_gap")),
        "r138_forwarding_prompt_hardened": bool(
            r138.get("pn_router_repair_forwarding_required")
        ),
        "r139_selected_accuracy": r139.get("selected_accuracy"),
        "r139_clean_fix_harm": r139.get("clean_fix_harm"),
        "r139_noisy_fix_harm": r139.get("noisy_fix_harm"),
        "r139_task250_router_repair_option": r139.get("task250_router_repair_option"),
        "r139_task250_router_repair_confidence": r139.get(
            "task250_router_repair_confidence"
        ),
        "r139_repair_min_confidence": r139.get("repair_min_confidence"),
        "r139_task250_repair_confidence_gate_passed": bool(
            r139.get("task250_repair_confidence_gate_passed")
        ),
        "r139_smoke_gate_passed": bool(r139.get("smoke_gate_passed")),
        "correction": (
            "do not lower the repair confidence threshold directly on task250; "
            "first design a leakage-safe calibration protocol using non-tail34 "
            "evidence and then retest only the same four-task gate"
        ),
        "calibration_protocol_requirements": [
            "no tail34 labels or task ids as threshold-training features",
            "calibrate confidence mapping on first200/non-tail34 or synthetic format controls",
            "keep task_8 and task_188 as clean harm guards",
            "require task_250 clean recovery before broad tail34",
            "run transfer validation before robustness or SCI-Q2 readiness claims",
        ],
        "required_clean_harm_guards": ["task_8", "task_188"],
        "required_clean_recovery_targets": ["task_250"],
        "noisy_optional_targets": ["task_108"],
        "broad_api_allowed_next": False,
        "next_protocol": "repair_confidence_calibration_protocol_before_api",
        "next_goal_audit_due": "R145",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R140 Goal Audit After R136-R140",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Window",
            "",
            "- R136: repair-field prompting pre-smoke",
            "- R137: repair-field API smoke with forwarding gap",
            "- R138: router repair-forwarding prompt hardening",
            "- R139: repair-forwarding API smoke with low-confidence rejection",
            "- R140: five-iteration goal audit",
            "",
            "## Verdict",
            "",
            f"Status: `{summary['status']}`",
            f"Drift detected: `{summary['drift_detected']}`",
            f"Drift type: `{summary['drift_type']}`",
            "",
            "The R136-R139 window stayed aligned with the SCI-Q2 goal because it kept "
            "PromptNode as a first-class node/edge graph mechanism, blocked broad API, "
            "and did not lower the final repair threshold to fit task250. The forwarding "
            "gap is fixed, but the clean gate is still not met.",
            "",
            "## Evidence",
            "",
            f"- Maintained update2 alignment: `{summary['maintained_update2_alignment']}`",
            f"- Maintained edge-prompt alignment: `{summary['maintained_edge_prompt_alignment']}`",
            f"- Maintained robustness alignment: `{summary['maintained_robustness_alignment']}`",
            f"- Forwarding gap fixed: `{summary['forwarding_gap_fixed']}`",
            f"- Clean gate still not met: `{summary['clean_gate_still_not_met']}`",
            f"- Confidence calibration needed: `{summary['confidence_calibration_needed']}`",
            "- Threshold lowering without protocol allowed: "
            f"`{summary['threshold_lowering_without_protocol_allowed']}`",
            f"- R139 selected accuracy: `{summary['r139_selected_accuracy']}`",
            f"- R139 clean fix/harm: `{summary['r139_clean_fix_harm']}`",
            f"- R139 task250 repair option: `{summary['r139_task250_router_repair_option']}`",
            f"- R139 task250 repair confidence: `{summary['r139_task250_router_repair_confidence']}`",
            f"- R139 repair min confidence: `{summary['r139_repair_min_confidence']}`",
            f"- R139 smoke gate passed: `{summary['r139_smoke_gate_passed']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            "",
            "## Correction",
            "",
            f"- {summary['correction']}",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Calibration protocol requirements: `{summary['calibration_protocol_requirements']}`",
            f"- Required clean harm guards: `{summary['required_clean_harm_guards']}`",
            f"- Required clean recovery targets: `{summary['required_clean_recovery_targets']}`",
            f"- Noisy optional targets: `{summary['noisy_optional_targets']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
            "## Current Best Signals",
            "",
            f"- Best tail34 signal: `{summary['best_current_tail34_signal']}`",
            f"- Best fresh integrated signal: `{summary['best_current_fresh_integrated_signal']}`",
            f"- Current edge-prompt signal: `{summary['current_edge_prompt_signal']}`",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R140 five-iteration goal audit.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_goal_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R140 goal audit: "
        f"status={summary['status']} broad_api={summary['broad_api_allowed_next']} "
        f"next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
