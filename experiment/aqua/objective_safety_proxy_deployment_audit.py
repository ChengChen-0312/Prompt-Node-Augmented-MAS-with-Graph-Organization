import argparse
import json
import os
import sys
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.objective_safety_proxy_protocol import REQUIRED_RULE_FEATURES  # noqa: E402


RULE_NAME = "r115_objective_safety_proxy_deployment_audit"
CLAIM_BOUNDARY = "deployment dependency audit only; no accuracy, cost-reduction, or API claim"

DEFAULT_R108_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r108_rank5_guard_deployability_summary.json"
)
DEFAULT_R109_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r109_objective_safety_rule_distillation_summary.json"
)
DEFAULT_R113_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r113_objective_safety_proxy_rule_summary.json"
)
DEFAULT_R114_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r114_objective_safety_proxy_regression_stress_summary.json"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r115_objective_safety_proxy_deployment_audit_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r115_objective_safety_proxy_deployment_audit_report.md"
)

OBJECTIVE_TRACE_FEATURES = [
    "objective_prediction_differs_from_baseline",
    "objective_top_score",
]
BASELINE_TRACE_FEATURES = ["baseline_direct_votes_split"]


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_proxy_deployment_audit_summary() -> Dict[str, Any]:
    r108 = _load_json(DEFAULT_R108_SUMMARY_JSON)
    r109 = _load_json(DEFAULT_R109_SUMMARY_JSON)
    r113 = _load_json(DEFAULT_R113_SUMMARY_JSON)
    r114 = _load_json(DEFAULT_R114_SUMMARY_JSON)
    rule_features = list(REQUIRED_RULE_FEATURES)
    objective_features = [
        feature for feature in rule_features if feature in OBJECTIVE_TRACE_FEATURES
    ]
    baseline_features = [
        feature for feature in rule_features if feature in BASELINE_TRACE_FEATURES
    ]
    requires_objective = bool(objective_features)
    single_template_guard_sufficient = bool(r108["single_template_guard_sufficient"])
    cheap_single_template_deployable = (
        single_template_guard_sufficient and not requires_objective
    )
    return {
        "rule": RULE_NAME,
        "learned_rule": r113["learned_rule"],
        "rule_features": rule_features,
        "rule_feature_count": len(rule_features),
        "features_requiring_objective_guided_trace": objective_features,
        "features_requiring_arg_baseline_trace": baseline_features,
        "requires_multiview_objective_features": bool(
            r109["requires_multiview_objective_features"]
        ),
        "single_template_guard_sufficient": single_template_guard_sufficient,
        "cheap_single_template_deployable": cheap_single_template_deployable,
        "cost_reduction_claim_ready": False,
        "prospective_api_ready": False,
        "supporting_positive_checks": {
            "r113_frozen_tail34_target_agreement": r113["frozen_tail34_target_agreement"],
            "r114_regression_action_agreement": r114["proxy_action_agreement_with_r107"],
            "r114_clean_fix_harm": r114["proxy_clean_fix_harm"],
        },
        "deployment_blockers": [
            "requires objective-guided multi-view trace features",
            "single rank5-template features were insufficient in R108",
            "no prospective API validation with the proxy has been run",
            "no measured cost reduction for proxy deployment exists",
        ],
        "input_field_violations": int(r113["proxy_input_field_violations"])
        + int(r114["proxy_input_field_violations"])
        + int(r109["rule_input_field_violations"]),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    blockers = [f"- {blocker}" for blocker in summary["deployment_blockers"]]
    return "\n".join(
        [
            "# R115 Objective-Safety Proxy Deployment Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Learned rule: `{summary['learned_rule']}`",
            f"- Rule features: `{summary['rule_features']}`",
            f"- Features requiring objective-guided trace: `{summary['features_requiring_objective_guided_trace']}`",
            f"- Features requiring ARG baseline trace: `{summary['features_requiring_arg_baseline_trace']}`",
            f"- Requires multi-view objective features: `{summary['requires_multiview_objective_features']}`",
            f"- Single-template guard sufficient: `{summary['single_template_guard_sufficient']}`",
            f"- Cheap single-template deployable: `{summary['cheap_single_template_deployable']}`",
            f"- Cost-reduction claim ready: `{summary['cost_reduction_claim_ready']}`",
            f"- Prospective API ready: `{summary['prospective_api_ready']}`",
            f"- Input-field violations: `{summary['input_field_violations']}`",
            "",
            "## Supporting Positive Checks",
            "",
            f"- R113 frozen target agreement: `{summary['supporting_positive_checks']['r113_frozen_tail34_target_agreement']}`",
            f"- R114 regression action agreement: `{summary['supporting_positive_checks']['r114_regression_action_agreement']}`",
            f"- R114 clean fix/harm: `{summary['supporting_positive_checks']['r114_clean_fix_harm']}`",
            "",
            "## Deployment Blockers",
            "",
            *blockers,
            "",
            "## Interpretation",
            "",
            "R115 prevents overclaiming the R113/R114 proxy as a cheap deployed method. The proxy is "
            "reproducible and passes the current regression stress, but it still depends on objective-guided "
            "multi-view trace features and has no prospective API or measured cost-reduction result.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit deployment dependencies for the objective-safety proxy.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_proxy_deployment_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R115 objective-safety proxy deployment audit: "
        f"cheap_single_template_deployable={summary['cheap_single_template_deployable']}"
    )


if __name__ == "__main__":
    main()
