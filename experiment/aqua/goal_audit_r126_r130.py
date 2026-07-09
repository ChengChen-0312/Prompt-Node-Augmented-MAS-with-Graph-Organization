import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r130_goal_audit_r126_r130"
CLAIM_BOUNDARY = "five-iteration goal audit and correction, not an accuracy result"

DEFAULT_R126_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r126_clean_fix_graph_policy_selector_protocol_summary.json"
)
DEFAULT_R127_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r127_clean_fix_graph_policy_selector_presmoke_summary.json"
)
DEFAULT_R128_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r128_rank5_high_fanin_selector_smoke_summary.json"
)
DEFAULT_R129_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r129_task250_router_none_failure_diagnosis_summary.json"
)
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r130_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r130_goal_audit_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_goal_audit_summary(
    r126_summary: str = DEFAULT_R126_SUMMARY,
    r127_summary: str = DEFAULT_R127_SUMMARY,
    r128_summary: str = DEFAULT_R128_SUMMARY,
    r129_summary: str = DEFAULT_R129_SUMMARY,
) -> Dict[str, Any]:
    r126 = _load_json(r126_summary)
    r127 = _load_json(r127_summary)
    r128 = _load_json(r128_summary)
    r129 = _load_json(r129_summary)

    maintained_update2_alignment = (
        not bool(r126.get("uses_tail34_training_source"))
        and not bool(r127.get("uses_tail34_outputs_for_rank_selection"))
        and r127.get("switches_with_update2_metadata") == 2
        and r127.get("switches_with_high_fanin_memory_bridge") == 2
        and r128.get("promptnode_graph_evidence_on_switches") == "2/2"
        and r128.get("switch_update2_metadata") == "2/2"
    )
    clean_gate_failed = (
        r128.get("clean_fix_harm") == "0/0"
        and not bool(r128.get("smoke_gate_passed"))
    )
    rank_only_path_invalidated = (
        r129.get("router_none_no_exact_runs") == "3/3"
        and r129.get("final_option_after_router_none_runs") == "3/3"
        and not bool(r129.get("rank_selection_sufficient"))
        and bool(r129.get("historical_success_is_nearest_choice_coercion"))
    )

    return {
        "rule": RULE_NAME,
        "status": "aligned_after_correction",
        "goal_window": ["R126", "R127", "R128", "R129", "R130"],
        "goal_reference": "SCI-Q2 PromptNode first-class graph goal in refine-logs/GOAL_SCI_Q2_PROMPTNODE_20260708.md and system goal",
        "drift_detected": True,
        "drift_type": "rank_only_high_fanin_path_mistook_final_coercion_for_clean_fix",
        "maintained_update2_alignment": maintained_update2_alignment,
        "clean_gate_failed": clean_gate_failed,
        "rank_only_path_invalidated": rank_only_path_invalidated,
        "r126_uses_tail34_training_source": bool(r126.get("uses_tail34_training_source")),
        "r126_broad_api_allowed_before_smoke": bool(r126.get("broad_api_allowed_before_smoke")),
        "r127_uses_tail34_outputs_for_rank_selection": bool(
            r127.get("uses_tail34_outputs_for_rank_selection")
        ),
        "r127_switch_tasks": r127.get("switch_tasks"),
        "r127_fallback_tasks": r127.get("fallback_tasks"),
        "r127_selected_template_ranks": r127.get("selected_template_ranks"),
        "r128_selected_accuracy": r128.get("selected_accuracy"),
        "r128_baseline_accuracy": r128.get("baseline_accuracy"),
        "r128_clean_fix_harm": r128.get("clean_fix_harm"),
        "r128_noisy_fix_harm": r128.get("noisy_fix_harm"),
        "r128_smoke_gate_passed": bool(r128.get("smoke_gate_passed")),
        "r129_router_none_no_exact_runs": r129.get("router_none_no_exact_runs"),
        "r129_final_option_after_router_none_runs": r129.get(
            "final_option_after_router_none_runs"
        ),
        "r129_historical_success_is_nearest_choice_coercion": bool(
            r129.get("historical_success_is_nearest_choice_coercion")
        ),
        "r129_rank_selection_sufficient": bool(r129.get("rank_selection_sufficient")),
        "correction": (
            "stop treating rank-5 high-fanin selection as a clean-recovery mechanism; harden "
            "final aggregation so PN_Router NONE/NO_EXACT_OPTION cannot be converted into an "
            "unsupported nearest-choice answer, or add an exact-option repair stage before selection"
        ),
        "next_protocol": "deterministic_none_guard_or_exact_option_repair_before_api",
        "implementation_priorities": [
            "deterministic_final_none_guard",
            "exact_option_repair_or_abstain_stage",
            "same_four_task_smoke_before_broad_tail34",
            "transfer_validation_after_clean_gate_passes",
        ],
        "required_clean_harm_guards": ["task_8", "task_188"],
        "required_clean_recovery_targets": ["task_250"],
        "noisy_optional_targets": ["task_108"],
        "broad_api_allowed_next": False,
        "next_goal_audit_due": "R135",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R130 Goal Audit After R126-R130",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Window",
            "",
            "- R126: leakage-safe clean-fix graph-policy selector protocol",
            "- R127: high-fanin explicit PromptNode selector pre-smoke",
            "- R128: bounded rank-5 high-fanin API smoke",
            "- R129: task250 router-NONE failure diagnosis",
            "- R130: five-iteration goal audit and correction",
            "",
            "## Verdict",
            "",
            f"Status: `{summary['status']}`",
            "",
            "R126-R129 stayed aligned with the update2 design by preserving first-class PromptNode "
            "graph evidence and preventing tail34 training leakage. The correction is about the next "
            "method step: the rank-only high-fanin route is now invalidated as a clean-recovery "
            "mechanism because `task_250` successes depend on final-layer option coercion after "
            "PN_Router abstention.",
            "",
            "## Evidence",
            "",
            f"- Maintained update2 alignment: `{summary['maintained_update2_alignment']}`",
            f"- R126 uses tail34 training source: `{summary['r126_uses_tail34_training_source']}`",
            f"- R127 uses tail34 outputs for rank selection: `{summary['r127_uses_tail34_outputs_for_rank_selection']}`",
            f"- R127 switch tasks: `{summary['r127_switch_tasks']}`",
            f"- R127 fallback tasks: `{summary['r127_fallback_tasks']}`",
            f"- R127 selected template ranks: `{summary['r127_selected_template_ranks']}`",
            f"- R128 selected accuracy: `{summary['r128_selected_accuracy']}`",
            f"- R128 baseline accuracy: `{summary['r128_baseline_accuracy']}`",
            f"- R128 clean fix/harm: `{summary['r128_clean_fix_harm']}`",
            f"- R128 noisy fix/harm: `{summary['r128_noisy_fix_harm']}`",
            f"- R128 smoke gate passed: `{summary['r128_smoke_gate_passed']}`",
            f"- R129 router NONE/NO_EXACT_OPTION runs: `{summary['r129_router_none_no_exact_runs']}`",
            f"- R129 final option after router NONE runs: `{summary['r129_final_option_after_router_none_runs']}`",
            f"- R129 historical success is nearest-choice coercion: `{summary['r129_historical_success_is_nearest_choice_coercion']}`",
            f"- R129 rank selection sufficient: `{summary['r129_rank_selection_sufficient']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            "",
            "## Drift Detected",
            "",
            f"`{summary['drift_type']}`",
            "",
            "The drift is not a loss of PromptNode graph evidence. It is the risk of interpreting "
            "rank-5 template selection or historical `task_250` success as a clean mechanism result. "
            "R129 shows that all compared rank-5 runs end with router abstention and then a forced "
            "final option, so this route must be corrected before another API smoke.",
            "",
            "## Correction",
            "",
            f"- {summary['correction']}",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Implementation priorities: `{summary['implementation_priorities']}`",
            f"- Required clean harm guards: `{summary['required_clean_harm_guards']}`",
            f"- Required clean recovery targets: `{summary['required_clean_recovery_targets']}`",
            f"- Noisy optional targets: `{summary['noisy_optional_targets']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R130 five-iteration goal audit.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_goal_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R130 goal audit: "
        f"status={summary['status']} broad_api={summary['broad_api_allowed_next']} "
        f"next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
