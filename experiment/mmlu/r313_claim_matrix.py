from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_AQUA_R266 = "experiment/aqua/res_logs/aqua_r266_audit_clean_rescore_summary.json"
DEFAULT_MMLU_R306 = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_MMLU_R309 = "experiment/mmlu/res_logs/mmlu_r309_negative_controls_summary.json"
DEFAULT_MMLU_R311 = "experiment/mmlu/res_logs/mmlu_r311_nonstem_promptnode_summary.json"
DEFAULT_MMLU_R312 = "experiment/mmlu/res_logs/mmlu_r312_nonstem_safety_replay_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r313_claim_matrix_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r313_claim_matrix_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_claim_matrix_summary(
    aqua_r266: str = DEFAULT_AQUA_R266,
    mmlu_r306: str = DEFAULT_MMLU_R306,
    mmlu_r309: str = DEFAULT_MMLU_R309,
    mmlu_r311: str = DEFAULT_MMLU_R311,
    mmlu_r312: str = DEFAULT_MMLU_R312,
) -> Dict[str, Any]:
    aqua = _load_json(aqua_r266)
    r306 = _load_json(mmlu_r306)
    r309 = _load_json(mmlu_r309)
    r311 = _load_json(mmlu_r311)
    r312 = _load_json(mmlu_r312)
    aqua_clean = aqua.get("scenarios", {}).get("exclude_59_139_228", {})
    aqua_task114_removed = aqua.get("scenarios", {}).get("exclude_59_139_228_114", {})

    evidence = {
        "aqua_audit_clean": {
            "baseline": aqua_clean.get("ARG", {}).get("accuracy", "unknown"),
            "proposed": aqua_clean.get("R065", {}).get("accuracy", "unknown"),
            "delta_correct": aqua_clean.get("delta", {}).get("delta_correct"),
            "claim": "positive_clean_improvement",
        },
        "aqua_conservative_remove_114": {
            "baseline": aqua_task114_removed.get("ARG", {}).get("accuracy", "unknown"),
            "proposed": aqua_task114_removed.get("R065", {}).get("accuracy", "unknown"),
            "delta_correct": aqua_task114_removed.get("delta", {}).get("delta_correct"),
            "claim": "positive_under_boundary_label_removal",
        },
        "mmlu_stem_main97": {
            "baseline": "88/97",
            "r304_symbolic": f"{r306.get('r304_main_correct', 0)}/{r306.get('main_records', 97)}",
            "proposed": f"{r306.get('main_correct', 0)}/{r306.get('main_records', 97)}",
            "delta_correct": 7,
            "fix_harm": "7/0",
            "cheap_control_threat": bool(r309.get("cheap_control_matches_or_beats_r306")),
            "equal_accuracy_more_cost_controls": r309.get("equal_accuracy_more_cost_controls", []),
            "claim": "positive_diagnostic_with_controls",
        },
        "mmlu_nonstem_raw": {
            "baseline": r311.get("arg_main", "unknown"),
            "proposed": r311.get("proposed_main", "unknown"),
            "delta_correct": r311.get("delta_vs_arg"),
            "fix_harm": r311.get("fix_harm_vs_arg"),
            "claim": "negative_transfer_without_warning_only_gate",
        },
        "mmlu_nonstem_safety_replay": {
            "baseline": r312.get("arg_main", "unknown"),
            "proposed": r312.get("proposed_safety_replay_main", "unknown"),
            "delta_correct": r312.get("delta_vs_arg"),
            "fix_harm": r312.get("fix_harm_vs_arg"),
            "claim": "no_harm_boundary_only",
        },
    }

    return {
        "run_id": "R313",
        "title": "Claim-evidence matrix after non-STEM transfer",
        "claim_boundary": (
            "R313 consolidates evidence only. It does not start training and does not convert diagnostic results "
            "into a final SCI-Q2 claim without ablations and prospective held-out validation."
        ),
        "no_api": True,
        "broad_api": False,
        "evidence": evidence,
        "paper_claim_draft": (
            "PromptNode/PromptEdge graph organization improves audited AQuA tail and MMLU STEM transfer, while "
            "non-STEM transfer currently supports only a warning-node no-harm boundary after lifecycle safety replay."
        ),
        "claim_permissions": {
            "aqua_clean_improvement_allowed": evidence["aqua_audit_clean"]["proposed"] == "31/31",
            "mmlu_stem_improvement_allowed": evidence["mmlu_stem_main97"]["proposed"] == "95/97"
            and not evidence["mmlu_stem_main97"]["cheap_control_threat"],
            "mmlu_nonstem_no_harm_allowed": evidence["mmlu_nonstem_safety_replay"]["fix_harm"] == "0/0",
            "mmlu_nonstem_improvement_allowed": False,
            "broad_general_promptnode_claim_allowed": False,
            "training_authorized": False,
            "sci_q2_ready": False,
        },
        "required_ablations": [
            "remove_safety_gate",
            "remove_lifecycle_prune",
            "remove_promptedge_text",
            "remove_nonmath_promptnodes",
            "remove_symbolic_verifier_family",
            "answer_bearing_vs_warning_only_promptnodes",
            "cost_matched_plain_requery",
        ],
        "next_required_run": "R314_goal_audit_after_r309_r313",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R313 Claim Matrix",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Evidence",
        "",
        "| Slice | Baseline | Proposed | Delta | Fix/Harm | Claim |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name, item in summary["evidence"].items():
        rows.append(
            f"| `{name}` | `{item.get('baseline', 'unknown')}` | `{item.get('proposed', 'unknown')}` | `{item.get('delta_correct', 'unknown')}` | `{item.get('fix_harm', '-')}` | {item.get('claim', '')} |"
        )
    rows.extend(["", "## Claim Permissions", ""])
    rows.extend(f"- `{name}`: `{value}`" for name, value in summary["claim_permissions"].items())
    rows.extend(["", "## Required Ablations", ""])
    rows.extend(f"- `{item}`" for item in summary["required_ablations"])
    rows.append("")
    return "\n".join(rows)


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_claim_matrix_summary()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R313 claim-evidence matrix.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
