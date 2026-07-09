import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r126_clean_fix_graph_policy_selector_protocol"
CLAIM_BOUNDARY = "protocol only; no training, API, accuracy, or cost result"

DEFAULT_R077_SUMMARY = "experiment/aqua/res_logs/aqua_first200_r077_clean_fix_graph_policy_distill_summary.json"
DEFAULT_R082_SUMMARY = "experiment/aqua/res_logs/aqua_first200_r082_clean_fix_graph_templates_summary.json"
DEFAULT_R112_SUMMARY = "experiment/aqua/res_logs/aqua_first200_r112_objective_safety_feature_export_summary.json"
DEFAULT_R125_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r125_goal_audit_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r126_clean_fix_graph_policy_selector_protocol_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r126_clean_fix_graph_policy_selector_protocol.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_clean_fix_graph_policy_selector_protocol(
    r077_summary: str = DEFAULT_R077_SUMMARY,
    r082_summary: str = DEFAULT_R082_SUMMARY,
    r112_summary: str = DEFAULT_R112_SUMMARY,
    r125_summary: str = DEFAULT_R125_SUMMARY,
) -> Dict[str, Any]:
    r077 = _load_json(r077_summary)
    r082 = _load_json(r082_summary)
    r112 = _load_json(r112_summary)
    r125 = _load_json(r125_summary)
    return {
        "rule": RULE_NAME,
        "protocol_only": True,
        "no_api_run": True,
        "r125_next_protocol": r125.get("next_protocol"),
        "allowed_training_sources": [
            "experiment/aqua/aqua_first200_r077_clean_fix_graph_policy_distill_rows.jsonl",
            "experiment/aqua/aqua_first200_r082_clean_fix_graph_templates.jsonl",
            "experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl",
        ],
        "forbidden_training_sources": [
            "tail34_r096_policy_targets",
            "tail34_r109_rule_distillation",
            "tail34_r113_eval_targets",
            "tail34_r114_regression_replay",
            "tail34_r124_outputs",
            "tail34_true_answers_or_clean_labels",
        ],
        "uses_tail34_training_source": False,
        "first200_template_count": int(r082.get("unique_templates") or 0),
        "first200_clean_fix_positive_rows": int(
            r082.get("positive_rows") or r077.get("clean_fix_preserve_rows") or 0
        ),
        "first200_objective_safety_rows": int(r112.get("num_rows") or 0),
        "first200_objective_safety_switch_targets": int(r112.get("switch_target_count") or 0),
        "candidate_selector_families": [
            "graph_policy_selector",
            "template_rank_policy",
            "guarded_multiview_distillation",
        ],
        "required_clean_harm_guards": ["task_8", "task_188"],
        "required_clean_recovery_targets": ["task_250"],
        "noisy_optional_targets": ["task_108"],
        "required_switch_evidence": [
            "explicit_promptnode_graph",
            "update2_metadata",
            "selector_input_violations_0",
            "no_tail34_training_source",
        ],
        "success_gate": {
            "selected_accuracy_at_least_baseline": True,
            "clean_harm_count": 0,
            "clean_fix_count_at_least": 1,
            "promptnode_evidence_on_switches": "all",
            "tail34_training_source": False,
        },
        "broad_api_allowed_before_smoke": False,
        "next_smoke_protocol": "four_task_clean_fix_graph_policy_selector_smoke",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R126 Clean-Fix Graph-Policy Selector Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Protocol only: `{summary['protocol_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Uses tail34 training source: `{summary['uses_tail34_training_source']}`",
            f"- First200 template count: `{summary['first200_template_count']}`",
            f"- First200 clean-fix positive rows: `{summary['first200_clean_fix_positive_rows']}`",
            f"- First200 objective-safety rows: `{summary['first200_objective_safety_rows']}`",
            f"- Candidate selector families: `{summary['candidate_selector_families']}`",
            f"- Required clean harm guards: `{summary['required_clean_harm_guards']}`",
            f"- Required clean recovery targets: `{summary['required_clean_recovery_targets']}`",
            f"- Noisy optional targets: `{summary['noisy_optional_targets']}`",
            f"- Broad API before smoke: `{summary['broad_api_allowed_before_smoke']}`",
            f"- Next smoke protocol: `{summary['next_smoke_protocol']}`",
            "",
            "## Allowed Training Sources",
            "",
            *[f"- `{item}`" for item in summary["allowed_training_sources"]],
            "",
            "## Forbidden Training Sources",
            "",
            *[f"- `{item}`" for item in summary["forbidden_training_sources"]],
            "",
            "## Interpretation",
            "",
            "R126 freezes the next path after the R125 audit. The next selector may learn from first200 "
            "clean-fix graph-policy/template artifacts and first200 objective-safety features, but tail34 "
            "artifacts may only be used as frozen evaluation or regression gates. The next API step remains "
            "blocked until a four-task clean-fix selector smoke is defined and passes.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R126 clean-fix graph-policy selector protocol.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_clean_fix_graph_policy_selector_protocol()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R126 clean-fix selector protocol: "
        f"templates={summary['first200_template_count']} "
        f"tail34_training={summary['uses_tail34_training_source']} "
        f"next={summary['next_smoke_protocol']}"
    )


if __name__ == "__main__":
    main()
