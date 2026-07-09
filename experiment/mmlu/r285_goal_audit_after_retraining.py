from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R281 = "experiment/mmlu/res_logs/mmlu_r281_training_protocol_freeze_summary.json"
DEFAULT_R282 = "experiment/mmlu/res_logs/mmlu_r282_arg_retrain_e5_observed_summary.json"
DEFAULT_R283 = "experiment/mmlu/res_logs/mmlu_r283_promptnode_retrain_e5_observed_summary.json"
DEFAULT_R284 = "experiment/mmlu/res_logs/mmlu_r284_retrained_graph_audit_compare_summary.json"
DEFAULT_SUMMARY = "experiment/mmlu/res_logs/mmlu_r285_goal_audit_after_retraining_summary.json"
DEFAULT_REPORT = "experiment/mmlu/run_logs/mmlu_r285_goal_audit_after_retraining_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        f.write(text)


def build_goal_audit(
    r281: Dict[str, Any],
    r282: Dict[str, Any],
    r283: Dict[str, Any],
    r284: Dict[str, Any],
) -> Dict[str, Any]:
    pn_roles = set(r283.get("pn_roles_present") or [])
    protocol_followed = bool(r281.get("training_authorized_next"))
    clean_arg = int(r282.get("role_mapping_size", 0)) == 6 and not r282.get("pn_roles_present")
    promptnode_trained = int(r283.get("role_mapping_size", 0)) >= 9 and {
        "PN_Memory",
        "PN_Verifier",
        "PN_Router",
    }.issubset(pn_roles)
    promptnode_generates_pn = float(r284.get("promptnode", {}).get("any_pn_rate", 0.0)) > 0.0
    structural_ready = bool(r284.get("structural_claim_supported"))

    blockers: List[str] = []
    if not protocol_followed:
        blockers.append("R281 protocol freeze is missing or did not authorize retraining.")
    if not clean_arg:
        blockers.append("R282 ARG baseline is not cleanly separated from PromptNode roles.")
    if not promptnode_trained:
        blockers.append("R283 PromptNode model did not train with all required PN roles.")
    if promptnode_trained and promptnode_generates_pn and not structural_ready:
        blockers.append(
            "R284 shows PromptNode generation exists but full PN/PE contract structure is unstable."
        )

    goal_alignment = (
        "aligned_and_ready_for_api"
        if protocol_followed and clean_arg and promptnode_trained and structural_ready
        else "aligned_but_blocked_on_structure"
    )

    return {
        "run_id": "R285",
        "title": "Goal audit after MMLU ARG/PromptNode retraining",
        "claim_boundary": (
            "Goal audit only. It checks whether R281-R284 stayed aligned with the SCI-Q2 "
            "research goal and whether checkpoint-level API evaluation is justified."
        ),
        "no_api": True,
        "broad_api": False,
        "goal_alignment": goal_alignment,
        "protocol_followed": protocol_followed,
        "clean_arg_retrained": clean_arg,
        "promptnode_retrained_with_required_roles": promptnode_trained,
        "promptnode_generates_pn": promptnode_generates_pn,
        "promptnode_contract_ready_rate": r284.get("promptnode", {}).get("contract_ready_rate"),
        "promptnode_all_pn_roles_rate": r284.get("promptnode", {}).get("all_pn_roles_rate"),
        "structural_claim_supported": structural_ready,
        "api_eval_allowed_next": structural_ready,
        "sci_q2_ready": False,
        "main_decision": (
            "Do not run costly checkpoint-level API evaluation yet; first improve the "
            "train-time graph policy or decoding so generated PromptNode graphs contain "
            "the complete Memory -> Verifier -> Router contract path reliably."
        ),
        "blockers": blockers,
        "next_runs": [
            "R286_constrained_promptnode_decoding",
            "R287_promptnode_chain_retrain",
            "R288_no_api_graph_audit",
            "R289_checkpoint_level_api_eval_if_R288_passes",
            "R290_goal_audit",
        ],
    }


def render_report(summary: Dict[str, Any]) -> str:
    blockers = [f"- {item}" for item in summary["blockers"]] or ["- None"]
    return "\n".join(
        [
            "# R285 Goal Audit After Retraining",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Status",
            "",
            f"- Goal alignment: `{summary['goal_alignment']}`",
            f"- Protocol followed: `{summary['protocol_followed']}`",
            f"- Clean ARG retrained: `{summary['clean_arg_retrained']}`",
            f"- PromptNode retrained with required roles: `{summary['promptnode_retrained_with_required_roles']}`",
            f"- PromptNode generates PN: `{summary['promptnode_generates_pn']}`",
            f"- PromptNode all-PN-role rate: `{summary['promptnode_all_pn_roles_rate']}`",
            f"- PromptNode contract-ready rate: `{summary['promptnode_contract_ready_rate']}`",
            f"- API eval allowed next: `{summary['api_eval_allowed_next']}`",
            f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
            "",
            "## Blockers",
            "",
            *blockers,
            "",
            "## Decision",
            "",
            summary["main_decision"],
            "",
            "## Next Runs",
            "",
            *[f"- `{item}`" for item in summary["next_runs"]],
            "",
        ]
    )


def run(
    r281_json: str = DEFAULT_R281,
    r282_json: str = DEFAULT_R282,
    r283_json: str = DEFAULT_R283,
    r284_json: str = DEFAULT_R284,
    summary_json: str = DEFAULT_SUMMARY,
    report_md: str = DEFAULT_REPORT,
) -> Dict[str, Any]:
    summary = build_goal_audit(
        r281=_load_json(r281_json),
        r282=_load_json(r282_json),
        r283=_load_json(r283_json),
        r284=_load_json(r284_json),
    )
    summary.update(
        {
            "source_summaries": {
                "r281": r281_json,
                "r282": r282_json,
                "r283": r283_json,
                "r284": r284_json,
            },
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R285 retraining goal audit.")
    parser.add_argument("--r281_json", default=DEFAULT_R281)
    parser.add_argument("--r282_json", default=DEFAULT_R282)
    parser.add_argument("--r283_json", default=DEFAULT_R283)
    parser.add_argument("--r284_json", default=DEFAULT_R284)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY)
    parser.add_argument("--report_md", default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
