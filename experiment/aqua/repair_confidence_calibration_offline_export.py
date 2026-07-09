import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.repair_confidence_calibration_protocol import (  # noqa: E402
    CALIBRATION_FEATURES,
    CLAIM_BOUNDARY as R141_CLAIM_BOUNDARY,
)
from mas_framework.agents.final_decision import EDGE_REPAIR_MIN_CONFIDENCE  # noqa: E402


RULE_NAME = "r142_repair_confidence_calibration_offline_export"
CLAIM_BOUNDARY = (
    "offline calibration export only; no API, final-gate change, accuracy, "
    "transfer, robustness, or SCI-readiness claim"
)

DEFAULT_R139_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r139_edge_prompt_repair_forwarding_smoke_summary.json"
)
DEFAULT_OUTPUT_JSONL = (
    "experiment/aqua/aqua_tail34_r142_repair_confidence_synthetic_controls.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r142_repair_confidence_calibration_offline_export_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r142_repair_confidence_calibration_offline_export.md"
)

FORBIDDEN_TRAINING_FIELDS = {
    "task_id",
    "true_answer",
    "clean_label",
    "is_solved",
    "selected_is_solved",
    "baseline_is_solved",
    "tail34",
    "r139_task250",
}


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def calibrate_repair_confidence(features: Dict[str, Any]) -> float:
    status = str(features.get("repair_binding_status") or "").upper()
    raw_distance = features.get("repair_distance_ratio")
    distance = 1.0 if raw_distance is None else float(raw_distance)
    verifier_router_agreement = bool(features.get("verifier_router_repair_agreement"))
    direct_contradiction = bool(features.get("direct_majority_contradiction"))
    option_text_exactness = bool(features.get("option_text_exactness"))
    source_count = int(features.get("candidate_source_count") or 0)

    base_by_status = {
        "NUMERIC_NEAREST_WITH_TYPO_CHECK": 0.55,
        "NUMERIC_TYPO_REPAIR": 0.65,
        "SYMBOLIC_EQUIVALENCE_REPAIR": 0.70,
    }
    score = base_by_status.get(status, 0.20)
    if distance <= 0.0001:
        score += 0.25
    elif distance <= 0.001:
        score += 0.15
    else:
        score -= 0.20
    score += 0.10 if verifier_router_agreement else -0.25
    score += 0.05 if option_text_exactness else 0.0
    score += 0.05 if source_count >= 2 else 0.0
    if direct_contradiction:
        score -= 0.60
    return round(_clamp(score), 6)


def build_synthetic_control_rows() -> List[Dict[str, Any]]:
    controls = [
        {
            "control_id": "valid_numeric_nearest_close_agree",
            "repair_binding_status": "NUMERIC_NEAREST_WITH_TYPO_CHECK",
            "repair_distance_ratio": 0.00004,
            "repair_confidence_text_bucket": "moderate",
            "verifier_router_repair_agreement": True,
            "direct_majority_contradiction": False,
            "option_text_exactness": True,
            "candidate_source_count": 1,
            "numeric_distance_bucket": "tiny",
            "expected_accept": True,
        },
        {
            "control_id": "valid_numeric_typo_close_agree",
            "repair_binding_status": "NUMERIC_TYPO_REPAIR",
            "repair_distance_ratio": 0.0002,
            "repair_confidence_text_bucket": "moderate",
            "verifier_router_repair_agreement": True,
            "direct_majority_contradiction": False,
            "option_text_exactness": True,
            "candidate_source_count": 2,
            "numeric_distance_bucket": "small",
            "expected_accept": True,
        },
        {
            "control_id": "valid_symbolic_equivalence_agree",
            "repair_binding_status": "SYMBOLIC_EQUIVALENCE_REPAIR",
            "repair_distance_ratio": 0.0,
            "repair_confidence_text_bucket": "high",
            "verifier_router_repair_agreement": True,
            "direct_majority_contradiction": False,
            "option_text_exactness": True,
            "candidate_source_count": 2,
            "numeric_distance_bucket": "zero",
            "expected_accept": True,
        },
        {
            "control_id": "reject_direct_majority_contradiction",
            "repair_binding_status": "NUMERIC_NEAREST_WITH_TYPO_CHECK",
            "repair_distance_ratio": 0.00004,
            "repair_confidence_text_bucket": "moderate",
            "verifier_router_repair_agreement": True,
            "direct_majority_contradiction": True,
            "option_text_exactness": True,
            "candidate_source_count": 1,
            "numeric_distance_bucket": "tiny",
            "expected_accept": False,
        },
        {
            "control_id": "reject_large_distance",
            "repair_binding_status": "NUMERIC_NEAREST_WITH_TYPO_CHECK",
            "repair_distance_ratio": 0.03,
            "repair_confidence_text_bucket": "moderate",
            "verifier_router_repair_agreement": True,
            "direct_majority_contradiction": False,
            "option_text_exactness": True,
            "candidate_source_count": 1,
            "numeric_distance_bucket": "large",
            "expected_accept": False,
        },
        {
            "control_id": "reject_missing_verifier_router_agreement",
            "repair_binding_status": "NUMERIC_NEAREST_WITH_TYPO_CHECK",
            "repair_distance_ratio": 0.00004,
            "repair_confidence_text_bucket": "moderate",
            "verifier_router_repair_agreement": False,
            "direct_majority_contradiction": False,
            "option_text_exactness": False,
            "candidate_source_count": 0,
            "numeric_distance_bucket": "tiny",
            "expected_accept": False,
        },
    ]
    rows = []
    for control in controls:
        confidence = calibrate_repair_confidence(control)
        rows.append(
            {
                **control,
                "source_family": "synthetic_numeric_repair_controls",
                "calibrated_repair_confidence": confidence,
                "calibration_accept": confidence >= EDGE_REPAIR_MIN_CONFIDENCE,
                "calibration_reason": "status_distance_agreement_contradiction_score",
            }
        )
    return rows


def _contains_forbidden_training_field(row: Dict[str, Any]) -> bool:
    lowered_keys = {str(key).lower() for key in row}
    if lowered_keys & FORBIDDEN_TRAINING_FIELDS:
        return True
    return any(
        "tail34" in str(value).lower() or "r139_task250" in str(value).lower()
        for value in row.values()
    )


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _r139_eval_features(r139: Dict[str, Any]) -> Dict[str, Any]:
    task250 = next(row for row in r139["rows"] if row["task_id"] == "task_250")
    raw_distance = task250.get("router_repair_distance_ratio")
    return {
        "repair_binding_status": r139.get("task250_router_repair_binding_status"),
        "repair_distance_ratio": 1.0 if raw_distance is None else float(raw_distance),
        "repair_confidence_text_bucket": "moderate",
        "verifier_router_repair_agreement": bool(r139.get("task250_router_repair_forwarded")),
        "direct_majority_contradiction": False,
        "option_text_exactness": True,
        "candidate_source_count": 1,
        "numeric_distance_bucket": "tiny",
    }


def build_repair_confidence_calibration_offline_export(
    r139_summary: str = DEFAULT_R139_SUMMARY,
) -> Dict[str, Any]:
    r139 = _load_json(r139_summary)
    rows = build_synthetic_control_rows()
    accepted_positive = sum(
        1 for row in rows if row["expected_accept"] and row["calibration_accept"]
    )
    rejected_negative = sum(
        1 for row in rows if not row["expected_accept"] and not row["calibration_accept"]
    )
    r139_features = _r139_eval_features(r139)
    r139_calibrated_confidence = calibrate_repair_confidence(r139_features)
    return {
        "rule": RULE_NAME,
        "offline_export_only": True,
        "no_api_run": True,
        "r141_claim_boundary": R141_CLAIM_BOUNDARY,
        "uses_tail34_training_source": False,
        "direct_threshold_lowering_allowed": False,
        "synthetic_control_rows": len(rows),
        "accepted_positive_controls": accepted_positive,
        "rejected_negative_controls": rejected_negative,
        "forbidden_training_field_violations": sum(
            1 for row in rows if _contains_forbidden_training_field(row)
        ),
        "calibration_features": list(CALIBRATION_FEATURES),
        "training_rows_path": DEFAULT_OUTPUT_JSONL,
        "r139_task250_eval_only": True,
        "r139_task250_used_for_training": False,
        "r139_task250_calibrated_confidence": r139_calibrated_confidence,
        "r139_task250_calibration_would_pass": (
            r139_calibrated_confidence >= EDGE_REPAIR_MIN_CONFIDENCE
        ),
        "repair_min_confidence": EDGE_REPAIR_MIN_CONFIDENCE,
        "required_clean_harm_guards": ["task_8", "task_188"],
        "required_clean_recovery_targets": ["task_250"],
        "noisy_optional_targets": ["task_108"],
        "broad_api_allowed_next": False,
        "next_protocol": "calibrated_repair_final_gate_offline_replay",
        "claim_boundary": CLAIM_BOUNDARY,
        "rows": rows,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R142 Repair-Confidence Calibration Offline Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Offline export only: `{summary['offline_export_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Uses tail34 training source: `{summary['uses_tail34_training_source']}`",
            f"- Direct threshold lowering allowed: `{summary['direct_threshold_lowering_allowed']}`",
            f"- Synthetic control rows: `{summary['synthetic_control_rows']}`",
            f"- Accepted positive controls: `{summary['accepted_positive_controls']}`",
            f"- Rejected negative controls: `{summary['rejected_negative_controls']}`",
            f"- Forbidden training-field violations: `{summary['forbidden_training_field_violations']}`",
            f"- R139 task250 eval only: `{summary['r139_task250_eval_only']}`",
            f"- R139 task250 used for training: `{summary['r139_task250_used_for_training']}`",
            f"- R139 task250 calibrated confidence: `{summary['r139_task250_calibrated_confidence']}`",
            f"- R139 task250 calibration would pass: `{summary['r139_task250_calibration_would_pass']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Interpretation",
            "",
            "R142 exports synthetic calibration controls and verifies that no tail34-specific "
            "training field is present. The R139 task250 row is evaluated only as a diagnostic. "
            "This supports building an offline calibrated final-gate replay next, but it is "
            "not an accuracy result and does not change the production gate.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write R142 repair-confidence calibration offline export."
    )
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_repair_confidence_calibration_offline_export()
    _write_jsonl(args.output_jsonl, summary["rows"])
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R142 repair-confidence offline export: "
        f"rows={summary['synthetic_control_rows']} "
        f"violations={summary['forbidden_training_field_violations']} "
        f"r139_eval={summary['r139_task250_calibration_would_pass']}"
    )


if __name__ == "__main__":
    main()
