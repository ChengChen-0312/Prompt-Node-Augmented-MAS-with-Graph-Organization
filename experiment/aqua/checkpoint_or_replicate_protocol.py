import argparse
import json
import math
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r149_transfer_checkpoint_or_aqua_replicate_protocol"
CLAIM_BOUNDARY = (
    "checkpoint-or-replicate protocol only; AQuA next100 is PromptNode-family evidence, "
    "not same-method significance evidence for R147"
)

DEFAULT_R148_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r148_statistical_audit_transfer_preflight_summary.json"
DEFAULT_NEXT100_SUMMARY = "experiment/aqua/res_logs/aqua_next100_multi_contract_union_selector_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r149_checkpoint_or_replicate_protocol_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r149_checkpoint_or_replicate_protocol_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _ratio(successes: int, total: int) -> str:
    return f"{int(successes)}/{int(total)}"


def _mcnemar_exact_p_two_sided(improvements: int, regressions: int) -> float:
    discordant = improvements + regressions
    if discordant == 0:
        return 1.0
    smaller = min(improvements, regressions)
    tail = sum(math.comb(discordant, k) for k in range(smaller + 1)) * (0.5 ** discordant)
    return round(min(1.0, 2 * tail), 6)


def build_checkpoint_or_replicate_protocol_summary(
    r148_summary: str = DEFAULT_R148_SUMMARY,
    next100_summary: str = DEFAULT_NEXT100_SUMMARY,
) -> Dict[str, Any]:
    r148 = _load_json(r148_summary)
    next100 = _load_json(next100_summary)
    fixes = int(next100.get("fixes_vs_baseline") or 0)
    harms = int(next100.get("harms_vs_baseline") or 0)
    total = int(next100.get("total_tasks") or 0)
    baseline_solved = int(next100.get("baseline_solved_tasks") or 0)
    selected_solved = int(next100.get("solved_tasks") or 0)

    return {
        "rule": RULE_NAME,
        "claim_boundary": CLAIM_BOUNDARY,
        "transfer_checkpoint_available": bool(r148.get("mmlu_arg_checkpoint_available")),
        "transfer_branch_allowed": False,
        "transfer_blocker": "missing_compatible_mmlu_arg_checkpoint",
        "aqua_next100_replicate_available": os.path.exists(_repo_path(next100_summary)),
        "next100_selector": next100.get("selector"),
        "next100_total_tasks": total,
        "next100_baseline_accuracy": _ratio(baseline_solved, total),
        "next100_selected_accuracy": _ratio(selected_solved, total),
        "next100_delta_vs_baseline": int(next100.get("delta_vs_baseline") or 0),
        "next100_fix_harm": _ratio(fixes, harms),
        "next100_mcnemar_exact_p_two_sided": _mcnemar_exact_p_two_sided(fixes, harms),
        "next100_significant_at_0_05": (
            _mcnemar_exact_p_two_sided(fixes, harms) < 0.05
        ),
        "same_method_as_r147": False,
        "combined_significance_claim_allowed": False,
        "family_replicate_claim_allowed": True,
        "r150_goal_audit_required_next": True,
        "broad_api_allowed_next": False,
        "next_protocol": "r150_goal_audit_before_any_more_api",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R149 Transfer Checkpoint or AQuA Replicate Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Transfer Branch",
            "",
            f"- Transfer checkpoint available: `{summary['transfer_checkpoint_available']}`",
            f"- Transfer branch allowed: `{summary['transfer_branch_allowed']}`",
            f"- Transfer blocker: `{summary['transfer_blocker']}`",
            "",
            "## AQuA Replicate Branch",
            "",
            f"- AQuA next100 replicate available: `{summary['aqua_next100_replicate_available']}`",
            f"- next100 selector: `{summary['next100_selector']}`",
            f"- next100 baseline accuracy: `{summary['next100_baseline_accuracy']}`",
            f"- next100 selected accuracy: `{summary['next100_selected_accuracy']}`",
            f"- next100 delta vs baseline: `{summary['next100_delta_vs_baseline']}`",
            f"- next100 fix/harm: `{summary['next100_fix_harm']}`",
            f"- next100 McNemar exact p: `{summary['next100_mcnemar_exact_p_two_sided']}`",
            f"- next100 significant at 0.05: `{summary['next100_significant_at_0_05']}`",
            f"- Same method as R147: `{summary['same_method_as_r147']}`",
            f"- Combined significance claim allowed: `{summary['combined_significance_claim_allowed']}`",
            f"- Family replicate claim allowed: `{summary['family_replicate_claim_allowed']}`",
            "",
            "## Next Gate",
            "",
            f"- R150 goal audit required next: `{summary['r150_goal_audit_required_next']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "## Interpretation",
            "",
            "R149 keeps the project from overclaiming. Transfer cannot run without a compatible "
            "MMLU checkpoint. Existing AQuA next100 evidence is useful as PromptNode-family "
            "replication (`87/100` vs `82/100`, `5/0` fix/harm), but because it uses a "
            "different multi-contract selector, it cannot be combined with R147 as same-method "
            "statistical evidence. The next required step is the scheduled R150 goal audit.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build R149 transfer-checkpoint or AQuA-replicate protocol."
    )
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_checkpoint_or_replicate_protocol_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R149 checkpoint-or-replicate protocol: "
        f"transfer={summary['transfer_branch_allowed']} "
        f"next100={summary['next100_selected_accuracy']} audit={summary['r150_goal_audit_required_next']}"
    )


if __name__ == "__main__":
    main()
