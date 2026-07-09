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


RULE_NAME = "r110_objective_safety_proxy_protocol"
CLAIM_BOUNDARY = "protocol only; no trained proxy, accuracy, or SCI claim"

DEFAULT_R077_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_first200_r077_clean_fix_graph_policy_distill_summary.json"
DEFAULT_R078_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_first200_r078_clean_fix_selector_summary.json"
DEFAULT_R109_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r109_objective_safety_rule_distillation_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r110_objective_safety_proxy_protocol_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r110_objective_safety_proxy_protocol.md"

REQUIRED_RULE_FEATURES = [
    "objective_prediction_differs_from_baseline",
    "objective_top_score",
    "baseline_direct_votes_split",
]

PROXY_CANDIDATE_FAMILIES = ["lightweight_multiview_objective", "graph_policy_selector"]

FORBIDDEN_TAIL34_TRAINING_SOURCES = [
    "experiment/aqua/aqua_tail34_r096_objective_safety_policy_targets.jsonl",
    "experiment/aqua/res_logs/aqua_tail34_r109_objective_safety_rule_distillation_summary.json",
    "experiment/aqua/aqua_tail34_r106_rank5_regression_smoke_results.jsonl",
]


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_proxy_protocol_summary() -> Dict[str, Any]:
    r077 = _load_json(DEFAULT_R077_SUMMARY_JSON)
    r078 = _load_json(DEFAULT_R078_SUMMARY_JSON)
    r109 = _load_json(DEFAULT_R109_SUMMARY_JSON)
    return {
        "rule": RULE_NAME,
        "train_sources": [
            "experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl"
        ],
        "train_source_rows": int(r077["rows"]),
        "train_clean_fix_preserve_rows": int(r077["clean_fix_preserve_rows"]),
        "existing_selector_eval_agreement": float(r078["eval_metrics"]["accuracy"]),
        "tail34_eval_target_source": DEFAULT_R109_SUMMARY_JSON,
        "tail34_eval_target_rows": int(r109["num_rows"]),
        "tail34_training_allowed": False,
        "forbidden_tail34_training_sources": FORBIDDEN_TAIL34_TRAINING_SOURCES,
        "required_rule_features": REQUIRED_RULE_FEATURES,
        "proxy_candidate_families": PROXY_CANDIDATE_FAMILIES,
        "input_field_violations": int(r077["selector_input_violations"])
        + int(r078["input_field_violations"])
        + int(r109["rule_input_field_violations"]),
        "minimum_next_gate": (
            "train on first200/non-tail34 only; evaluate target agreement on frozen R109 tail34 "
            "rule targets; then run a small clean-harm/recovery smoke before broad API use"
        ),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    forbidden_rows = [f"- `{path}`" for path in summary["forbidden_tail34_training_sources"]]
    return "\n".join(
        [
            "# R110 Objective-Safety Proxy Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Train source rows: `{summary['train_source_rows']}`",
            f"- Train clean-fix preserve rows: `{summary['train_clean_fix_preserve_rows']}`",
            f"- Existing selector eval agreement: `{summary['existing_selector_eval_agreement']}`",
            f"- Tail34 eval target rows: `{summary['tail34_eval_target_rows']}`",
            f"- Tail34 training allowed: `{summary['tail34_training_allowed']}`",
            f"- Required rule features: `{summary['required_rule_features']}`",
            f"- Proxy candidate families: `{summary['proxy_candidate_families']}`",
            f"- Input field violations: `{summary['input_field_violations']}`",
            "",
            "## Forbidden Tail34 Training Sources",
            "",
            *forbidden_rows,
            "",
            "## Minimum Next Gate",
            "",
            summary["minimum_next_gate"],
            "",
            "## Interpretation",
            "",
            "R110 freezes the next proxy-training boundary. Tail34 R096/R109 can evaluate whether "
            "a proxy matches the objective-safety rule, but those rows cannot be training examples. "
            "This keeps the SCI-Q2 story defensible by separating method iteration, proxy training, "
            "and held-out validation.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Freeze the objective-safety proxy training protocol.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_proxy_protocol_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R110 objective-safety proxy protocol: "
        f"train_rows={summary['train_source_rows']} "
        f"tail34_training_allowed={summary['tail34_training_allowed']}"
    )


if __name__ == "__main__":
    main()
