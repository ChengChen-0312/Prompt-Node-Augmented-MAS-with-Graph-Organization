import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r117_lightweight_objective_trace_protocol"
CLAIM_BOUNDARY = "protocol only; no new accuracy, cost, or API result"

DEFAULT_R068_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r068_selective_multiview_summary.json"
DEFAULT_R074_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r074_surgical_cascade_summary.json"
DEFAULT_R116_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r116_objective_safety_baseline_only_trigger_audit_summary.json"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r117_lightweight_objective_trace_protocol_summary.json"
)
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r117_lightweight_objective_trace_protocol.md"


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_lightweight_objective_trace_protocol_summary() -> Dict[str, Any]:
    r068 = _load_json(DEFAULT_R068_SUMMARY_JSON)
    r074 = _load_json(DEFAULT_R074_SUMMARY_JSON)
    r116 = _load_json(DEFAULT_R116_SUMMARY_JSON)
    full_multiview_cost = round(float(r068["cost_estimate"]["full_multiview_cost"]), 6)
    measured_cost_target = round(float(r074["cost"]), 6)
    return {
        "rule": RULE_NAME,
        "protocol_only": True,
        "no_api_run": True,
        "llm_name": "gpt-4o-2024-08-06",
        "candidate_protocols": ["two_view_objective_probe", "graph_policy_topk_probe"],
        "regression_tasks": ["task_8", "task_108", "task_188", "task_250"],
        "required_suppressed_harm_tasks": ["task_8"],
        "required_clean_recovery_tasks": ["task_250"],
        "required_no_clean_harm": True,
        "minimum_regression_guarded_solved": "4/4",
        "baseline_only_trigger_allowed": bool(r116["baseline_only_proxy_sufficient"]),
        "tail34_training_allowed": False,
        "broad_api_allowed_before_smoke": False,
        "max_promptnode_views_per_triggered_task": 2,
        "full_multiview_cost_reference": full_multiview_cost,
        "measured_cost_target_upper_bound": measured_cost_target,
        "cost_gate": (
            "measured total cost must be below R074 measured cost and far below full multi-view "
            "before an efficiency claim is allowed"
        ),
        "accuracy_gate": (
            "four-task smoke must preserve R114 behavior: suppress task_8 harm, recover task_250, "
            "and introduce no clean harm"
        ),
        "forbidden_shortcuts": [
            "baseline_only_direct_vote_trigger",
            "single_rank5_template_guard",
            "tail34_training_or_threshold_tuning",
            "broad_api_before_regression_smoke",
        ],
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    forbidden = [f"- `{item}`" for item in summary["forbidden_shortcuts"]]
    return "\n".join(
        [
            "# R117 Lightweight Objective-Trace Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Protocol only: `{summary['protocol_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Model: `{summary['llm_name']}`",
            f"- Candidate protocols: `{summary['candidate_protocols']}`",
            f"- Regression tasks: `{summary['regression_tasks']}`",
            f"- Required suppressed harms: `{summary['required_suppressed_harm_tasks']}`",
            f"- Required clean recoveries: `{summary['required_clean_recovery_tasks']}`",
            f"- No clean harm required: `{summary['required_no_clean_harm']}`",
            f"- Baseline-only trigger allowed: `{summary['baseline_only_trigger_allowed']}`",
            f"- Tail34 training allowed: `{summary['tail34_training_allowed']}`",
            f"- Broad API before smoke: `{summary['broad_api_allowed_before_smoke']}`",
            f"- Max PromptNode views per triggered task: `{summary['max_promptnode_views_per_triggered_task']}`",
            f"- Full multi-view cost reference: `${summary['full_multiview_cost_reference']:.6f}`",
            f"- Measured cost target upper bound: `${summary['measured_cost_target_upper_bound']:.6f}`",
            "",
            "## Gates",
            "",
            f"- Cost: {summary['cost_gate']}",
            f"- Accuracy: {summary['accuracy_gate']}",
            "",
            "## Forbidden Shortcuts",
            "",
            *forbidden,
            "",
            "## Interpretation",
            "",
            "R117 freezes the next prospective direction without spending API. It requires a lightweight "
            "objective-trace or graph-policy signal because R116 rejected baseline-only triggers, and it "
            "blocks broad evaluation until the four-task clean-harm/recovery smoke passes with measured cost.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Freeze a lightweight objective-trace protocol.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_lightweight_objective_trace_protocol_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R117 lightweight objective-trace protocol: "
        f"max_views={summary['max_promptnode_views_per_triggered_task']} "
        f"cost_bound=${summary['measured_cost_target_upper_bound']:.6f}"
    )


if __name__ == "__main__":
    main()
