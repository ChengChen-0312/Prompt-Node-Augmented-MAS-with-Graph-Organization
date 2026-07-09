import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r150_goal_audit_r146_r150"
CLAIM_BOUNDARY = "five-iteration goal audit and correction; not an accuracy or readiness result"

DEFAULT_R146_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r146_calibrated_repair_smoke_summary.json"
DEFAULT_R147_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r147_frozen_selector_replay_summary.json"
DEFAULT_R148_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r148_statistical_audit_transfer_preflight_summary.json"
DEFAULT_R149_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r149_checkpoint_or_replicate_protocol_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r150_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r150_goal_audit_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_goal_audit_summary(
    r146_summary: str = DEFAULT_R146_SUMMARY,
    r147_summary: str = DEFAULT_R147_SUMMARY,
    r148_summary: str = DEFAULT_R148_SUMMARY,
    r149_summary: str = DEFAULT_R149_SUMMARY,
) -> Dict[str, Any]:
    r146 = _load_json(r146_summary)
    r147 = _load_json(r147_summary)
    r148 = _load_json(r148_summary)
    r149 = _load_json(r149_summary)

    maintained_update2_alignment = (
        r146.get("promptnode_graph_evidence_on_switches") == "2/2"
        and r146.get("switch_update2_metadata") == "2/2"
        and r147.get("promptnode_graph_evidence_on_switches") == "2/2"
        and r147.get("switch_update2_metadata") == "2/2"
    )
    maintained_edge_prompt_alignment = (
        r146.get("decision_method") == "CalibratedEdgePromptRepairContractFinalRefer"
        and bool(r146.get("task250_router_repair_forwarded"))
        and bool(r146.get("task250_calibrated_repair_gate_passed"))
    )
    claim_discipline_maintained = (
        not bool(r147.get("fresh_integrated_full_run"))
        and not bool(r148.get("statistically_significant_at_0_05"))
        and not bool(r148.get("cost_normalized_superiority_supported"))
        and not bool(r149.get("combined_significance_claim_allowed"))
        and not bool(r149.get("broad_api_allowed_next"))
    )

    return {
        "rule": RULE_NAME,
        "status": "aligned_but_not_sci_q2_ready",
        "goal_window": ["R146", "R147", "R148", "R149", "R150"],
        "drift_detected": False,
        "drift_type": "none_claims_constrained_after_positive_smoke",
        "maintained_update2_alignment": maintained_update2_alignment,
        "maintained_edge_prompt_alignment": maintained_edge_prompt_alignment,
        "claim_discipline_maintained": claim_discipline_maintained,
        "r146_smoke_gate_passed": bool(r146.get("smoke_gate_passed")),
        "r146_clean_fix_harm": r146.get("clean_fix_harm"),
        "r147_selected_accuracy": r147.get("selected_accuracy"),
        "r147_clean_fix_harm": r147.get("clean_fix_harm"),
        "r147_fresh_integrated_full_run": bool(r147.get("fresh_integrated_full_run")),
        "r148_statistically_significant_at_0_05": bool(
            r148.get("statistically_significant_at_0_05")
        ),
        "r148_mcnemar_exact_p_two_sided": r148.get("mcnemar_exact_p_two_sided"),
        "r148_cost_normalized_superiority_supported": bool(
            r148.get("cost_normalized_superiority_supported")
        ),
        "r148_mmlu_arg_checkpoint_available": bool(
            r148.get("mmlu_arg_checkpoint_available")
        ),
        "r149_transfer_branch_allowed": bool(r149.get("transfer_branch_allowed")),
        "r149_family_replicate_claim_allowed": bool(
            r149.get("family_replicate_claim_allowed")
        ),
        "r149_same_method_as_r147": bool(r149.get("same_method_as_r147")),
        "sci_q2_ready": False,
        "blocking_gaps": [
            "R147 full-tail34 evidence is replay-level, not a fresh integrated full run",
            "R148 McNemar p=0.5 is not statistically significant",
            "R148 cost-normalized superiority is unsupported",
            "MMLU transfer is blocked by missing compatible ARG checkpoint",
            "AQuA next100 is family evidence, not same-method R147 significance",
        ],
        "broad_api_allowed_next": False,
        "next_protocol": "r151_sci_q2_evidence_gap_plan_before_more_api",
        "next_goal_audit_due": "R155",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R150 Five-Iteration Goal Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Status: `{summary['status']}`",
            f"- Goal window: `{summary['goal_window']}`",
            f"- Drift detected: `{summary['drift_detected']}`",
            f"- Drift type: `{summary['drift_type']}`",
            f"- Maintained update2 alignment: `{summary['maintained_update2_alignment']}`",
            f"- Maintained edge-prompt alignment: `{summary['maintained_edge_prompt_alignment']}`",
            f"- Claim discipline maintained: `{summary['claim_discipline_maintained']}`",
            f"- R146 smoke gate passed: `{summary['r146_smoke_gate_passed']}`",
            f"- R147 selected accuracy: `{summary['r147_selected_accuracy']}`",
            f"- R148 McNemar p: `{summary['r148_mcnemar_exact_p_two_sided']}`",
            f"- R148 cost-normalized superiority: `{summary['r148_cost_normalized_superiority_supported']}`",
            f"- R149 transfer branch allowed: `{summary['r149_transfer_branch_allowed']}`",
            f"- R149 family replicate claim allowed: `{summary['r149_family_replicate_claim_allowed']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            f"- Next goal audit due: `{summary['next_goal_audit_due']}`",
            "",
            "## Blocking Gaps",
            "",
            *[f"- {gap}" for gap in summary["blocking_gaps"]],
            "",
            "## Interpretation",
            "",
            "R146-R149 stayed aligned with the user's PromptNode/update2 direction because positive "
            "smoke evidence was followed by replay, statistical audit, and transfer-blocker checks "
            "instead of broad overclaiming. The project is not SCI-Q2 ready yet. The next step must "
            "be an evidence-gap plan before additional API or manuscript-level claims.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write R150 five-iteration goal audit.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_goal_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R150 goal audit: "
        f"status={summary['status']} sci={summary['sci_q2_ready']} "
        f"broad={summary['broad_api_allowed_next']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
