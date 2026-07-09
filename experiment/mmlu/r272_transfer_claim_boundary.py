from __future__ import annotations

import json
import os
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_R254_SUMMARY = os.path.join(SCRIPT_DIR, "res_logs", "mmlu_r254_mmlu_transfer_result_analysis_summary.json")
DEFAULT_R259_SUMMARY = os.path.join(SCRIPT_DIR, "res_logs", "mmlu_r259_promptnode_v2_api_summary.json")
DEFAULT_R261_REPORT = os.path.join(SCRIPT_DIR, "run_logs", "mmlu_r261_result_to_claim_after_transfer_v2.md")
DEFAULT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "res_logs", "mmlu_r272_transfer_claim_boundary_summary.json")
DEFAULT_REPORT_MD = os.path.join(SCRIPT_DIR, "run_logs", "mmlu_r272_transfer_claim_boundary.md")


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build_r272_transfer_boundary() -> Dict[str, Any]:
    r254 = load_json(DEFAULT_R254_SUMMARY)
    r259 = load_json(DEFAULT_R259_SUMMARY)
    r254_assessment = r254["assessment"]
    r259_variant = r259["by_variant"]["proposed_v2_independent_guarded_pnpe"]
    arg_v2 = r259["by_variant"]["arg_baseline_fixed"]
    v2_no_harm = int(r259_variant["harms"]) == 0
    v2_beats_arg = int(r259_variant["correct"]) > int(arg_v2["correct"])
    return {
        "run_id": "R272",
        "title": "MMLU transfer claim boundary",
        "dataset": "MMLU STEM tiny16 transfer diagnostic",
        "claim_boundary": "non_aqua_transfer_completed_but_superiority_not_supported",
        "non_aqua_transfer_completed": True,
        "r254_v1": {
            "arg_baseline": "8/16",
            "proposed": "10/16",
            "plain_requery": "12/16",
            "node_only": "11/16",
            "proposed_fix_harm": "3/1",
            "transfer_superiority_supported": bool(r254_assessment["transfer_superiority_supported"]),
            "proposed_beats_plain_requery": bool(r254_assessment["proposed_beats_plain_requery"]),
            "proposed_beats_node_only": bool(r254_assessment["proposed_beats_node_only"]),
        },
        "r259_v2": {
            "arg_baseline": f"{arg_v2['correct']}/{arg_v2['records']}",
            "proposed_v2": f"{r259_variant['correct']}/{r259_variant['records']}",
            "fix_harm": f"{r259_variant['fixes']}/{r259_variant['harms']}",
            "beats_arg": v2_beats_arg,
            "no_harm": v2_no_harm,
            "api_cost": r259.get("api_cost"),
        },
        "transfer_superiority_supported": False,
        "no_significant_harm_supported_for_v2_tiny": v2_no_harm,
        "claim_revision": "narrow_to_aqua_with_mmlu_negative_transfer_boundary",
        "paper_use": (
            "Use MMLU as a negative transfer and robustness boundary: current PN/PE prompts can improve over fixed ARG on tiny16 but do not beat plain requery or node-only controls. Main claims must stay on AQuA official/audit-clean evidence."
        ),
        "stop_after_this_run": True,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R272 MMLU Transfer Claim Boundary",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Transfer Results",
            "",
            f"- R254 v1 proposed: `{summary['r254_v1']['proposed']}`; ARG `{summary['r254_v1']['arg_baseline']}`; plain `{summary['r254_v1']['plain_requery']}`; node-only `{summary['r254_v1']['node_only']}`",
            f"- R259 v2 proposed: `{summary['r259_v2']['proposed_v2']}`; ARG `{summary['r259_v2']['arg_baseline']}`; fix/harm `{summary['r259_v2']['fix_harm']}`",
            f"- Transfer superiority supported: `{summary['transfer_superiority_supported']}`",
            f"- V2 no-harm on tiny diagnostic: `{summary['no_significant_harm_supported_for_v2_tiny']}`",
            "",
            "## Claim Revision",
            "",
            summary["paper_use"],
            "",
            f"Stop after this run: `{summary['stop_after_this_run']}`",
            "",
        ]
    )


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_r272_transfer_boundary()
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
