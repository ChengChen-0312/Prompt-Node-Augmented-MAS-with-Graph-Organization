import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r125_goal_audit_r121_r125"
CLAIM_BOUNDARY = "five-iteration goal audit and correction, not an accuracy result"

DEFAULT_R121_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r121_guarded_two_view_probe_protocol_summary.json"
DEFAULT_R122_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r122_guarded_two_view_probe_replay_summary.json"
DEFAULT_R123_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r123_explicit_promptnode_template_preflight_summary.json"
DEFAULT_R124_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r124_explicit_template_guarded_smoke_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r125_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r125_goal_audit_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_goal_audit_summary(
    r121_summary: str = DEFAULT_R121_SUMMARY,
    r122_summary: str = DEFAULT_R122_SUMMARY,
    r123_summary: str = DEFAULT_R123_SUMMARY,
    r124_summary: str = DEFAULT_R124_SUMMARY,
) -> Dict[str, Any]:
    r121 = _load_json(r121_summary)
    r122 = _load_json(r122_summary)
    r123 = _load_json(r123_summary)
    r124 = _load_json(r124_summary)
    recovered_update2_evidence = (
        r123.get("candidate_tasks_with_update2_metadata") == "4/4"
        and r124.get("promptnode_graph_evidence_on_switches") == "2/2"
        and r124.get("switch_update2_metadata") == "2/2"
    )
    clean_fix_gate_failed = r124.get("clean_fix_harm") == "0/0" and not r124.get(
        "smoke_gate_passed"
    )
    return {
        "rule": RULE_NAME,
        "status": "aligned_after_correction",
        "goal_window": ["R121", "R122", "R123", "R124", "R125"],
        "drift_detected": True,
        "drift_type": "rank1_explicit_template_path_restores_update2_evidence_but_fails_clean_fix_gate",
        "r121_explicit_promptnode_required": bool(r121.get("explicit_promptnode_evidence_required")),
        "r122_update2_evidence_ready": bool(r122.get("update2_evidence_ready")),
        "r123_candidate_update2_metadata": r123.get("candidate_tasks_with_update2_metadata"),
        "r123_forbidden_field_violations": r123.get("candidate_tasks_with_forbidden_field_violations"),
        "r124_selected_accuracy": r124.get("selected_accuracy"),
        "r124_baseline_accuracy": r124.get("baseline_accuracy"),
        "r124_fix_harm": r124.get("fix_harm"),
        "r124_clean_fix_harm": r124.get("clean_fix_harm"),
        "r124_noisy_fix_harm": r124.get("noisy_fix_harm"),
        "r124_promptnode_graph_evidence_on_switches": r124.get("promptnode_graph_evidence_on_switches"),
        "r124_switch_update2_metadata": r124.get("switch_update2_metadata"),
        "r124_smoke_gate_passed": bool(r124.get("smoke_gate_passed")),
        "r124_broad_api_allowed_next": bool(r124.get("broad_api_allowed_next")),
        "recovered_update2_evidence": recovered_update2_evidence,
        "clean_fix_gate_failed": clean_fix_gate_failed,
        "correction": (
            "demote rank1 explicit-template selection to mechanism evidence; do not broaden API; "
            "train or select a graph/template policy that recovers clean task_250 while preserving "
            "task_8 and task_188 clean guards"
        ),
        "broad_api_allowed_next": False,
        "next_protocol": "train_or_select_clean_fix_graph_policy_before_smoke",
        "required_clean_harm_guards": ["task_8", "task_188"],
        "required_clean_recovery_targets": ["task_250"],
        "allowed_evidence_sources_next": [
            "first200_non_tail34_graph_policy_training",
            "explicit_promptnode_template_metadata",
            "guarded_multi_view_objective_features_without_tail34_training",
        ],
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R125 Goal Audit After R121-R125",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Window",
            "",
            "- R121: guarded two-view / graph-policy protocol",
            "- R122: strict update2 replay checker",
            "- R123: explicit PromptNode template preflight",
            "- R124: explicit-template guarded smoke",
            "- R125: goal audit and correction",
            "",
            "## Verdict",
            "",
            f"Status: `{summary['status']}`",
            "",
            "R121-R124 remained aligned with the update2 design because they restored first-class "
            "PromptNode graph evidence before switching. The new correction is methodological: rank-1 "
            "explicit templates are not enough for the SCI-Q2 clean-reasoning claim because the smoke "
            "recovers only noisy `task_108` and misses clean `task_250`.",
            "",
            "## Evidence",
            "",
            f"- R123 candidate update2 metadata: `{summary['r123_candidate_update2_metadata']}`",
            f"- R123 forbidden-field violations: `{summary['r123_forbidden_field_violations']}`",
            f"- R124 selected accuracy: `{summary['r124_selected_accuracy']}`",
            f"- R124 baseline accuracy: `{summary['r124_baseline_accuracy']}`",
            f"- R124 fix/harm: `{summary['r124_fix_harm']}`",
            f"- R124 clean fix/harm: `{summary['r124_clean_fix_harm']}`",
            f"- R124 noisy fix/harm: `{summary['r124_noisy_fix_harm']}`",
            f"- R124 PromptNode graph evidence on switches: `{summary['r124_promptnode_graph_evidence_on_switches']}`",
            f"- R124 switch update2 metadata: `{summary['r124_switch_update2_metadata']}`",
            f"- R124 smoke gate passed: `{summary['r124_smoke_gate_passed']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            "",
            "## Drift Detected",
            "",
            f"`{summary['drift_type']}`",
            "",
            "The drift risk is no longer missing virtual-node evidence. It is over-promoting a rank-1 "
            "explicit-template path that satisfies update2 metadata requirements but does not recover a clean "
            "reasoning fix. For SCI-Q2, this must stay as a negative boundary unless a selector or trained "
            "graph policy recovers clean `task_250` without harming `task_8` or `task_188`.",
            "",
            "## Correction",
            "",
            f"- {summary['correction']}",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Required clean harm guards: `{summary['required_clean_harm_guards']}`",
            f"- Required clean recovery targets: `{summary['required_clean_recovery_targets']}`",
            f"- Allowed evidence sources next: `{summary['allowed_evidence_sources_next']}`",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R125 five-iteration goal audit.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_goal_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R125 goal audit: "
        f"status={summary['status']} broad_api={summary['broad_api_allowed_next']} "
        f"next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
