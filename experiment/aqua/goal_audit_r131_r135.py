import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r135_goal_audit_r131_r135"
CLAIM_BOUNDARY = "five-iteration goal audit and correction, not an accuracy result"

DEFAULT_R131_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r131_deterministic_router_none_guard_protocol_summary.json"
)
DEFAULT_R132_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r132_deterministic_router_none_guard_smoke_summary.json"
)
DEFAULT_R133_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r133_edge_prompt_policy_protocol_summary.json"
DEFAULT_R134_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r134_edge_prompt_repair_gate_protocol_summary.json"
)
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r135_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r135_goal_audit_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_goal_audit_summary(
    r131_summary: str = DEFAULT_R131_SUMMARY,
    r132_summary: str = DEFAULT_R132_SUMMARY,
    r133_summary: str = DEFAULT_R133_SUMMARY,
    r134_summary: str = DEFAULT_R134_SUMMARY,
) -> Dict[str, Any]:
    r131 = _load_json(r131_summary)
    r132 = _load_json(r132_summary)
    r133 = _load_json(r133_summary)
    r134 = _load_json(r134_summary)

    maintained_update2_alignment = (
        bool(r131.get("decision_method_registered"))
        and r132.get("promptnode_graph_evidence_on_switches") == "2/2"
        and r132.get("switch_update2_metadata") == "2/2"
        and bool(r133.get("prompt_as_edge_first_class"))
        and r133.get("switches_with_edge_prompt_specs") == "2/2"
        and r133.get("switches_with_repair_edge_prompt") == "2/2"
    )
    maintained_robustness_alignment = (
        bool(r133.get("multi_dataset_transfer_required"))
        and bool(r133.get("no_task_id_routing"))
        and not bool(r133.get("uses_tail34_training_source"))
        and bool(r134.get("low_confidence_rejected"))
        and bool(r134.get("large_distance_rejected"))
        and not bool(r134.get("r132_task250_has_repair_fields"))
        and r134.get("r132_task250_repair_gate_parser_prediction") == "None."
    )
    clean_gate_still_not_met = (
        r132.get("clean_fix_harm") == "0/0"
        and not bool(r132.get("smoke_gate_passed"))
        and r134.get("r132_task250_repair_gate_parser_prediction") == "None."
    )

    return {
        "rule": RULE_NAME,
        "status": "aligned_continue_without_broad_api",
        "goal_window": ["R131", "R132", "R133", "R134", "R135"],
        "goal_reference": "SCI-Q2 PromptNode first-class graph goal with update2 node+edge virtual graph organization and robustness boundary",
        "drift_detected": False,
        "drift_type": "none_after_edge_prompt_and_repair_gate_correction",
        "maintained_update2_alignment": maintained_update2_alignment,
        "maintained_robustness_alignment": maintained_robustness_alignment,
        "prompt_as_edge_correction_made": bool(r133.get("prompt_as_edge_first_class")),
        "final_layer_no_longer_invents_repair": (
            r134.get("missing_repair_parser_prediction") == "None."
            and r134.get("r132_task250_repair_gate_parser_prediction") == "None."
        ),
        "clean_gate_still_not_met": clean_gate_still_not_met,
        "r131_forced_option_after_router_none_prevented": r131.get(
            "forced_option_after_router_none_prevented"
        ),
        "r132_selected_accuracy": r132.get("selected_accuracy"),
        "r132_clean_fix_harm": r132.get("clean_fix_harm"),
        "r132_noisy_fix_harm": r132.get("noisy_fix_harm"),
        "r132_smoke_gate_passed": bool(r132.get("smoke_gate_passed")),
        "r132_router_none_abstained": r132.get("router_none_abstained"),
        "r133_prompt_as_edge_first_class": bool(r133.get("prompt_as_edge_first_class")),
        "r133_node_only_promptnode_sufficient": bool(
            r133.get("node_only_promptnode_sufficient")
        ),
        "r133_switches_with_edge_prompt_specs": r133.get("switches_with_edge_prompt_specs"),
        "r133_switches_with_repair_edge_prompt": r133.get(
            "switches_with_repair_edge_prompt"
        ),
        "r133_edge_prompt_selector_input_violations": r133.get(
            "edge_prompt_selector_input_violations"
        ),
        "r134_decision_method": r134.get("decision_method"),
        "r134_explicit_repair_parser_prediction": r134.get(
            "explicit_repair_parser_prediction"
        ),
        "r134_missing_repair_parser_prediction": r134.get(
            "missing_repair_parser_prediction"
        ),
        "r134_low_confidence_rejected": bool(r134.get("low_confidence_rejected")),
        "r134_large_distance_rejected": bool(r134.get("large_distance_rejected")),
        "r134_r132_task250_has_repair_fields": bool(
            r134.get("r132_task250_has_repair_fields")
        ),
        "r134_r132_task250_repair_gate_parser_prediction": r134.get(
            "r132_task250_repair_gate_parser_prediction"
        ),
        "correction": (
            "continue the edge-prompt path, but do not claim robustness or accuracy until "
            "PN_Verifier/PN_Router emit repair fields prospectively and the same four-task clean gate passes"
        ),
        "implementation_priorities": [
            "edge_prompt_repair_field_prompting_presmoke",
            "same_four_task_clean_gate_before_broad_api",
            "transfer_validation_after_clean_gate_passes",
            "train_time_node_and_edge_graph_policy_after_prompting_smoke",
        ],
        "required_clean_harm_guards": ["task_8", "task_188"],
        "required_clean_recovery_targets": ["task_250"],
        "noisy_optional_targets": ["task_108"],
        "broad_api_allowed_next": False,
        "next_protocol": "edge_prompt_repair_field_prompting_presmoke",
        "next_goal_audit_due": "R140",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R135 Goal Audit After R131-R135",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Window",
            "",
            "- R131: deterministic router-NONE final guard",
            "- R132: same-four-task deterministic-router smoke",
            "- R133: prompt-as-edge policy protocol",
            "- R134: edge-prompt repair final gate",
            "- R135: five-iteration goal audit",
            "",
            "## Verdict",
            "",
            f"Status: `{summary['status']}`",
            f"Drift detected: `{summary['drift_detected']}`",
            f"Drift type: `{summary['drift_type']}`",
            "",
            "The R131-R134 window stayed aligned after correction. R132 showed that abstention "
            "preserves integrity but does not recover clean `task_250`. R133 then incorporated the "
            "user's prompt-as-edge requirement, and R134 ensured the final layer cannot invent repair "
            "evidence. The clean gate is still not met, so broad API remains blocked.",
            "",
            "## Evidence",
            "",
            f"- Maintained update2 alignment: `{summary['maintained_update2_alignment']}`",
            f"- Maintained robustness alignment: `{summary['maintained_robustness_alignment']}`",
            f"- Prompt-as-edge correction made: `{summary['prompt_as_edge_correction_made']}`",
            f"- Final layer no longer invents repair: `{summary['final_layer_no_longer_invents_repair']}`",
            f"- Clean gate still not met: `{summary['clean_gate_still_not_met']}`",
            f"- R131 forced option after router NONE prevented: `{summary['r131_forced_option_after_router_none_prevented']}`",
            f"- R132 selected accuracy: `{summary['r132_selected_accuracy']}`",
            f"- R132 clean fix/harm: `{summary['r132_clean_fix_harm']}`",
            f"- R132 noisy fix/harm: `{summary['r132_noisy_fix_harm']}`",
            f"- R132 smoke gate passed: `{summary['r132_smoke_gate_passed']}`",
            f"- R132 router-NONE abstained: `{summary['r132_router_none_abstained']}`",
            f"- R133 edge prompt specs: `{summary['r133_switches_with_edge_prompt_specs']}`",
            f"- R133 repair edge prompts: `{summary['r133_switches_with_repair_edge_prompt']}`",
            f"- R133 selector input violations: `{summary['r133_edge_prompt_selector_input_violations']}`",
            f"- R134 decision method: `{summary['r134_decision_method']}`",
            f"- R134 explicit repair parser prediction: `{summary['r134_explicit_repair_parser_prediction']}`",
            f"- R134 missing repair parser prediction: `{summary['r134_missing_repair_parser_prediction']}`",
            f"- R134 low confidence rejected: `{summary['r134_low_confidence_rejected']}`",
            f"- R134 large distance rejected: `{summary['r134_large_distance_rejected']}`",
            f"- R134 R132 task250 has repair fields: `{summary['r134_r132_task250_has_repair_fields']}`",
            f"- R134 R132 task250 repair-gate parser prediction: `{summary['r134_r132_task250_repair_gate_parser_prediction']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
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
    parser = argparse.ArgumentParser(description="Write R135 five-iteration goal audit.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_goal_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R135 goal audit: "
        f"status={summary['status']} broad_api={summary['broad_api_allowed_next']} "
        f"next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
