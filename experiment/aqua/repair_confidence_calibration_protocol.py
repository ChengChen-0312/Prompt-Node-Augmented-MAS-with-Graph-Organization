import argparse
import json
import os
import sys
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r141_repair_confidence_calibration_protocol"
CLAIM_BOUNDARY = (
    "calibration protocol only; no API, threshold change, accuracy, transfer, "
    "robustness, or SCI-readiness claim"
)

DEFAULT_R139_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r139_edge_prompt_repair_forwarding_smoke_summary.json"
)
DEFAULT_R140_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r140_goal_audit_summary.json"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r141_repair_confidence_calibration_protocol_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r141_repair_confidence_calibration_protocol.md"
)

ALLOWED_SOURCES = [
    "first200_non_tail34_option_binding_audit",
    "first200_non_tail34_graph_policy_rows",
    "first200_non_tail34_objective_safety_features",
    "synthetic_numeric_repair_controls",
]

FORBIDDEN_SOURCES = [
    "tail34_true_answers_or_clean_labels",
    "tail34_task_ids",
    "tail34_r096_r109_r113_eval_targets_as_training",
    "r137_or_r139_switch_predictions_as_training_labels",
    "r139_task250_confidence_as_threshold_target",
]

CALIBRATION_FEATURES = [
    "repair_binding_status",
    "repair_distance_ratio",
    "repair_confidence_text_bucket",
    "verifier_router_repair_agreement",
    "direct_majority_contradiction",
    "option_text_exactness",
    "candidate_source_count",
    "numeric_distance_bucket",
]

SUCCESS_GATES = [
    "offline_calibration_uses_no_forbidden_source",
    "same_four_task_clean_harm_0_on_task_8_task_188",
    "same_four_task_clean_recovery_task_250",
    "same_four_task_noisy_task_108_not_regressed",
    "broad_tail34_still_blocked_until_four_task_gate_passes",
]


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_repair_confidence_calibration_protocol(
    r139_summary: str = DEFAULT_R139_SUMMARY,
    r140_summary: str = DEFAULT_R140_SUMMARY,
) -> Dict[str, Any]:
    r139 = _load_json(r139_summary)
    r140 = _load_json(r140_summary)
    r139_forwarding_fixed = bool(r139.get("task250_router_repair_forwarded")) and not bool(
        r139.get("verifier_router_repair_forwarding_gap")
    )
    r139_low_confidence_rejection = bool(
        r139.get("task250_repair_forwarded_but_rejected_low_confidence")
    )
    return {
        "rule": RULE_NAME,
        "protocol_only": True,
        "no_api_run": True,
        "r140_alignment_confirmed": (
            r140.get("status") == "aligned_continue_with_calibration_protocol"
            and not bool(r140.get("drift_detected"))
        ),
        "r139_forwarding_fixed": r139_forwarding_fixed,
        "r139_low_confidence_rejection": r139_low_confidence_rejection,
        "r139_task250_repair_confidence": r139.get("task250_router_repair_confidence"),
        "r139_repair_min_confidence": r139.get("repair_min_confidence"),
        "direct_threshold_lowering_allowed": False,
        "uses_tail34_training_source": False,
        "allowed_sources": list(ALLOWED_SOURCES),
        "forbidden_sources": list(FORBIDDEN_SOURCES),
        "calibration_features": list(CALIBRATION_FEATURES),
        "success_gates": list(SUCCESS_GATES),
        "calibration_output_contract": {
            "fields": [
                "repair_option",
                "repair_binding_status",
                "calibrated_repair_confidence",
                "calibration_reason",
                "calibration_source_family",
            ],
            "must_preserve_abstention_when": [
                "direct_majority_contradiction",
                "distance_ratio_above_bound",
                "missing_verifier_router_agreement",
            ],
        },
        "required_clean_harm_guards": ["task_8", "task_188"],
        "required_clean_recovery_targets": ["task_250"],
        "noisy_optional_targets": ["task_108"],
        "same_four_task_smoke_allowed_after_offline_export": True,
        "broad_api_allowed_next": False,
        "next_protocol": "repair_confidence_calibration_offline_export",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    def _bullets(values: List[str]) -> List[str]:
        return [f"- `{value}`" for value in values]

    return "\n".join(
        [
            "# R141 Repair-Confidence Calibration Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Protocol only: `{summary['protocol_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- R140 alignment confirmed: `{summary['r140_alignment_confirmed']}`",
            f"- R139 forwarding fixed: `{summary['r139_forwarding_fixed']}`",
            f"- R139 low-confidence rejection: `{summary['r139_low_confidence_rejection']}`",
            f"- R139 task250 repair confidence: `{summary['r139_task250_repair_confidence']}`",
            f"- R139 repair min confidence: `{summary['r139_repair_min_confidence']}`",
            f"- Direct threshold lowering allowed: `{summary['direct_threshold_lowering_allowed']}`",
            f"- Uses tail34 training source: `{summary['uses_tail34_training_source']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Allowed Sources",
            "",
            *_bullets(summary["allowed_sources"]),
            "",
            "## Forbidden Sources",
            "",
            *_bullets(summary["forbidden_sources"]),
            "",
            "## Calibration Features",
            "",
            *_bullets(summary["calibration_features"]),
            "",
            "## Success Gates",
            "",
            *_bullets(summary["success_gates"]),
            "",
            "## Interpretation",
            "",
            "R141 does not change the final repair threshold. It freezes a non-leaky "
            "calibration route so any future confidence change is supported by non-tail34 "
            "evidence or synthetic controls rather than task250-specific tuning. The next "
            "step is an offline export/checker before any further API smoke.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write R141 repair-confidence calibration protocol."
    )
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_repair_confidence_calibration_protocol()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R141 repair-confidence calibration protocol: "
        f"tail34_training={summary['uses_tail34_training_source']} "
        f"broad={summary['broad_api_allowed_next']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
