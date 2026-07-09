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


RULE_NAME = "r121_guarded_two_view_or_graph_policy_probe_protocol"
CLAIM_BOUNDARY = "protocol only; no new API, accuracy, or cost result"

DEFAULT_R120_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r120_goal_audit_summary.json"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r121_guarded_two_view_probe_protocol_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r121_guarded_two_view_probe_protocol.md"
)

REGRESSION_TASKS = ["task_8", "task_108", "task_188", "task_250"]


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_guarded_two_view_probe_protocol_summary(
    r120_summary_json: str = DEFAULT_R120_SUMMARY_JSON,
) -> Dict[str, Any]:
    r120 = _load_json(r120_summary_json)
    r119_promptnode_graph_hits = r120["r119_promptnode_graph_hits"]
    r119_strong_router_contract_rows = r120["r119_strong_router_contract_rows"]
    return {
        "rule": RULE_NAME,
        "protocol_only": True,
        "no_api_run": True,
        "regression_tasks": list(REGRESSION_TASKS),
        "candidate_protocols": [
            "guarded_router_calibrated_two_view",
            "guarded_candidate_calibrated_two_view",
            "train_time_graph_policy_probe",
        ],
        "max_promptnode_views_per_task": 2,
        "broad_api_allowed_before_smoke": False,
        "explicit_promptnode_evidence_required": True,
        "strong_contract_or_two_view_agreement_required": True,
        "blocks_direct_vote_only_switches": True,
        "r119_clean_harm_blocked_by_protocol": (
            r119_promptnode_graph_hits == "0/4"
            and r119_strong_router_contract_rows == "0/4"
            and "task_250" in r120.get("r119_clean_harm_tasks", [])
        ),
        "r119_promptnode_graph_hits": r119_promptnode_graph_hits,
        "r119_strong_router_contract_rows": r119_strong_router_contract_rows,
        "r119_clean_harm_tasks": r120.get("r119_clean_harm_tasks", []),
        "r119_drift_type": r120.get("drift_type"),
        "required_gate_checks": [
            "no_switch_without_explicit_promptnode_graph_or_strong_contract",
            "no_switch_without_two_view_nonbaseline_agreement_unless_graph_policy_confident",
            "no_broad_api_before_same_four_task_smoke_passes",
            "same_model_gpt_4o_2024_08_06",
            "tail34_artifacts_not_training_data",
        ],
        "pass_conditions": {
            "selected_accuracy_at_least_internal_arg": True,
            "clean_harm_count": 0,
            "policy_input_violations": 0,
            "promptnode_evidence_on_switches": True,
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R121 Guarded Two-View / Graph-Policy Probe Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Protocol only: `{summary['protocol_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Regression tasks: `{summary['regression_tasks']}`",
            f"- Candidate protocols: `{summary['candidate_protocols']}`",
            f"- Max PromptNode views per task: `{summary['max_promptnode_views_per_task']}`",
            f"- Broad API before smoke: `{summary['broad_api_allowed_before_smoke']}`",
            f"- Explicit PromptNode evidence required: `{summary['explicit_promptnode_evidence_required']}`",
            f"- Strong contract or two-view agreement required: `{summary['strong_contract_or_two_view_agreement_required']}`",
            f"- Blocks direct-vote-only switches: `{summary['blocks_direct_vote_only_switches']}`",
            f"- R119 clean harm blocked by protocol: `{summary['r119_clean_harm_blocked_by_protocol']}`",
            f"- R119 PromptNode graph hits: `{summary['r119_promptnode_graph_hits']}`",
            f"- R119 strong router-contract rows: `{summary['r119_strong_router_contract_rows']}`",
            "",
            "## Required Gate Checks",
            "",
            *[f"- `{item}`" for item in summary["required_gate_checks"]],
            "",
            "## Interpretation",
            "",
            "R121 corrects the R119 drift before spending more API. The next smoke must not switch "
            "when the only support is a calibrated direct-vote signal without explicit PromptNode graph "
            "or strong router-contract evidence. This keeps the method aligned with the update2 first-class "
            "virtual-node design.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Freeze R121 guarded probe protocol.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_guarded_two_view_probe_protocol_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R121 guarded two-view protocol: "
        f"blocks_r119={summary['r119_clean_harm_blocked_by_protocol']}"
    )


if __name__ == "__main__":
    main()
