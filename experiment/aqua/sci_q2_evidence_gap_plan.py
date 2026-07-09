import argparse
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r151_sci_q2_evidence_gap_plan_before_more_api"
CLAIM_BOUNDARY = "evidence-gap plan only; no new experiment, API run, or readiness claim"

DEFAULT_R150_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r150_goal_audit_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r151_sci_q2_evidence_gap_plan_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r151_sci_q2_evidence_gap_plan.md"
DEFAULT_REFINE_PLAN_MD = "refine-logs/SCI_Q2_EVIDENCE_GAP_PLAN_R151_20260708.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def build_evidence_gap_plan_summary(
    r150_summary: str = DEFAULT_R150_SUMMARY,
) -> Dict[str, Any]:
    r150 = _load_json(r150_summary)
    must_run_blocks = [
        "transfer_checkpoint_resolution",
        "same_method_aqua_replicate",
        "cost_normalized_variant_or_accounting",
        "negative_control_ablations",
        "paper_claim_and_citation_audit",
    ]
    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "plan_only": True,
        "no_api_run": True,
        "source_goal_audit": r150_summary,
        "sci_q2_ready": False,
        "blocking_gaps": r150["blocking_gaps"],
        "blocking_gap_count": len(r150["blocking_gaps"]),
        "must_run_blocks": must_run_blocks,
        "transfer_required_for_sci_q2": True,
        "same_method_significance_required": True,
        "cost_boundary_required": True,
        "minimum_same_method_gate": {
            "fresh_or_pre_registered_replay": "required",
            "paired_test": "McNemar exact or larger-split paired bootstrap",
            "target": "p < 0.05 or report as exploratory only",
            "no_clean_harm": True,
            "promptnode_update2_evidence_on_switches": "all",
        },
        "transfer_gate": {
            "required_artifact": "compatible MMLU ARG checkpoint or explicitly scoped no-transfer paper",
            "split": "experiment/mmlu/mmlu_stem_transfer100.jsonl",
            "allowed_api_before_checkpoint": False,
        },
        "cost_gate": {
            "preferred": "selected_correct_per_dollar >= ARG baseline",
            "fallback_wording": "accuracy-cost tradeoff, not cost-normalized superiority",
        },
        "broad_api_allowed_next": False,
        "preflight_allowed_next": True,
        "next_protocol": "r152_mmlu_checkpoint_resolution_or_aqua_same_method_replicate_preflight",
    }


def render_plan(summary: Dict[str, Any]) -> str:
    blocks = {
        "transfer_checkpoint_resolution": (
            "Resolve transfer blocker",
            "Find or build a compatible MMLU ARG checkpoint, then run the fixed STEM100 split.",
            "No transfer claim until the checkpoint exists and the run completes.",
        ),
        "same_method_aqua_replicate": (
            "Same-method AQuA replicate",
            "Freeze the R147 selector/method and evaluate it on a larger pre-registered split.",
            "Use paired significance; exploratory if p >= 0.05.",
        ),
        "cost_normalized_variant_or_accounting": (
            "Cost boundary",
            "Either reduce incremental PromptNode cost or explicitly frame the method as accuracy-cost tradeoff.",
            "Do not claim cost-normalized superiority unless correct-per-dollar improves.",
        ),
        "negative_control_ablations": (
            "Negative controls",
            "Run no-router, no-lifecycle, random PN, dense PN, and node-only/no-edge ablations.",
            "Show PromptNode node+edge organization matters beyond answer repair.",
        ),
        "paper_claim_and_citation_audit": (
            "Paper audit",
            "Run claim-evidence and citation audits before drafting SCI-Q2 claims.",
            "Every numeric claim must map to raw logs.",
        ),
    }
    table = [
        f"| `{key}` | {blocks[key][0]} | {blocks[key][1]} | {blocks[key][2]} |"
        for key in summary["must_run_blocks"]
    ]
    return "\n".join(
        [
            "# R151 SCI-Q2 Evidence-Gap Plan",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Current Verdict",
            "",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            f"- Plan only: `{summary['plan_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Blocking Gaps",
            "",
            *[f"- {gap}" for gap in summary["blocking_gaps"]],
            "",
            "## Must-Run Blocks",
            "",
            "| Block | Purpose | Run | Success Boundary |",
            "| --- | --- | --- | --- |",
            *table,
            "",
            "## Gates",
            "",
            f"- Transfer required for SCI-Q2: `{summary['transfer_required_for_sci_q2']}`",
            f"- Same-method significance required: `{summary['same_method_significance_required']}`",
            f"- Cost boundary required: `{summary['cost_boundary_required']}`",
            f"- Same-method target: `{summary['minimum_same_method_gate']['target']}`",
            f"- Transfer split: `{summary['transfer_gate']['split']}`",
            f"- Cost fallback wording: `{summary['cost_gate']['fallback_wording']}`",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build R151 SCI-Q2 evidence-gap plan.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--refine-plan-md", default=DEFAULT_REFINE_PLAN_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_evidence_gap_plan_summary()
    plan = render_plan(summary)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), plan)
    write_text(_repo_path(args.refine_plan_md), plan)
    print(
        "Built R151 evidence-gap plan: "
        f"gaps={summary['blocking_gap_count']} next={summary['next_protocol']}"
    )


if __name__ == "__main__":
    main()
