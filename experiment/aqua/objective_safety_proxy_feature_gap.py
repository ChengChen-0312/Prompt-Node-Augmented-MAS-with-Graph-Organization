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


RULE_NAME = "r111_objective_safety_proxy_feature_gap"
CLAIM_BOUNDARY = "feature coverage audit only; no proxy training or accuracy claim"

DEFAULT_R078_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_first200_r078_clean_fix_selector_summary.json"
DEFAULT_R110_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r110_objective_safety_proxy_protocol_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r111_objective_safety_proxy_feature_gap_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r111_objective_safety_proxy_feature_gap_report.md"


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_feature_gap_summary() -> Dict[str, Any]:
    r078 = _load_json(DEFAULT_R078_SUMMARY_JSON)
    r110 = _load_json(DEFAULT_R110_SUMMARY_JSON)
    required = list(r110["required_rule_features"])
    existing = list(r078["feature_names"])
    existing_set = set(existing)
    covered = [feature for feature in required if feature in existing_set]
    missing = [feature for feature in required if feature not in existing_set]
    return {
        "rule": RULE_NAME,
        "required_feature_count": len(required),
        "existing_r078_feature_count": len(existing),
        "required_rule_features": required,
        "existing_r078_features": existing,
        "directly_covered_required_features": covered,
        "missing_required_features": missing,
        "proxy_training_ready": len(missing) == 0,
        "recommended_next_artifact": "first200_objective_safety_feature_export",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    missing_rows = [f"- `{feature}`" for feature in summary["missing_required_features"]]
    return "\n".join(
        [
            "# R111 Objective-Safety Proxy Feature Gap",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Required feature count: `{summary['required_feature_count']}`",
            f"- Existing R078 feature count: `{summary['existing_r078_feature_count']}`",
            f"- Directly covered required features: `{summary['directly_covered_required_features']}`",
            f"- Proxy training ready: `{summary['proxy_training_ready']}`",
            f"- Recommended next artifact: `{summary['recommended_next_artifact']}`",
            "",
            "## Missing Required Features",
            "",
            *missing_rows,
            "",
            "## Interpretation",
            "",
            "R078 is useful evidence that first200 graph-policy targets are learnable, but it is not "
            "a valid proxy for the R109 objective-safety rule. The required objective-vs-baseline and "
            "direct-split fields must be exported for first200/non-tail34 data before training the "
            "R110 proxy.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit feature coverage for the R110 proxy protocol.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_feature_gap_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R111 objective-safety proxy feature gap: "
        f"missing={summary['missing_required_features']}"
    )


if __name__ == "__main__":
    main()
