from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R313_SUMMARY = "experiment/mmlu/res_logs/mmlu_r313_claim_matrix_summary.json"
DEFAULT_R319_SUMMARY = "experiment/mmlu/res_logs/mmlu_r319_ablation_table_update_summary.json"
DEFAULT_R320_SUMMARY = "experiment/mmlu/res_logs/mmlu_r320_goal_audit_after_ablations_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r321_paper_evidence_table_and_training_gate_report.md"


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


def _row(
    slice_name: str,
    baseline: str,
    promptnode: str,
    delta_correct: Any,
    fix_harm: str,
    paper_claim: str,
    note: str,
) -> Dict[str, Any]:
    return {
        "slice": slice_name,
        "baseline": baseline,
        "promptnode": promptnode,
        "delta_correct": delta_correct,
        "fix_harm": fix_harm,
        "paper_claim": paper_claim,
        "note": note,
    }


def build_main_results(evidence: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    aqua = evidence.get("aqua_audit_clean", {})
    aqua_conservative = evidence.get("aqua_conservative_remove_114", {})
    mmlu_stem = evidence.get("mmlu_stem_main97", {})
    nonstem_safe = evidence.get("mmlu_nonstem_safety_replay", {})
    nonstem_raw = evidence.get("mmlu_nonstem_raw", {})
    return [
        _row(
            "AQuA_audit_clean_tail31",
            aqua.get("baseline", "unknown"),
            aqua.get("proposed", "unknown"),
            aqua.get("delta_correct"),
            aqua.get("fix_harm", "-"),
            "positive_clean_improvement",
            "Audit-clean after excluding task_59/task_139/task_228.",
        ),
        _row(
            "AQuA_conservative_remove_114_tail30",
            aqua_conservative.get("baseline", "unknown"),
            aqua_conservative.get("proposed", "unknown"),
            aqua_conservative.get("delta_correct"),
            aqua_conservative.get("fix_harm", "-"),
            "positive_under_boundary_label_removal",
            "Sensitivity check if task_114 is treated as a boundary label case.",
        ),
        _row(
            "MMLU_STEM_main97",
            mmlu_stem.get("baseline", "unknown"),
            mmlu_stem.get("proposed", "unknown"),
            mmlu_stem.get("delta_correct"),
            mmlu_stem.get("fix_harm", "-"),
            "positive_with_completed_controls",
            "R306 keeps +7 correct over ARG after negative controls and ablations.",
        ),
        _row(
            "MMLU_nonSTEM40_safety_replay",
            nonstem_safe.get("baseline", "unknown"),
            nonstem_safe.get("proposed", "unknown"),
            nonstem_safe.get("delta_correct"),
            nonstem_safe.get("fix_harm", "-"),
            "no_harm_boundary_only",
            "Warning-only semantic nodes cannot be claimed as non-STEM improvement.",
        ),
        _row(
            "MMLU_nonSTEM40_raw_warning_override",
            nonstem_raw.get("baseline", "unknown"),
            nonstem_raw.get("proposed", "unknown"),
            nonstem_raw.get("delta_correct"),
            nonstem_raw.get("fix_harm", "-"),
            "negative_transfer_limitation",
            "This row belongs in limitations or appendix, not as a main positive result.",
        ),
    ]


def build_selector_training_gate(r319: Dict[str, Any], r320: Dict[str, Any]) -> Dict[str, Any]:
    priority_done = not r319.get("priority_pending_ablations")
    claim_permissions = r320.get("claim_permissions", {})
    return {
        "preflight_authorized": bool(priority_done),
        "execute_training_authorized": False,
        "reason_execution_blocked": (
            "A prospective train/dev/test split and leakage check must be frozen before selector training can run."
        ),
        "allowed_training_target": (
            "Learn a graph-policy selector for PromptNode type, PromptEdge read/write/forward permission, and lifecycle "
            "action; do not train a direct answer predictor."
        ),
        "required_features": [
            "arg_node_state_features",
            "promptnode_type_features",
            "promptedge_text_features",
            "read_write_forward_permission_features",
            "lifecycle_action_features",
            "budget_and_cost_features",
            "agreement_conflict_features",
        ],
        "forbidden_training_signals": [
            "ground_truth_answer_text",
            "label_audited_noisy_items",
            "warning_only_promptnode_override",
            "dataset_specific_task_id_rules",
            "posthoc_wrong_item_memorization",
        ],
        "minimum_success_criteria_for_execution": {
            "heldout_positive_slice": "Beat ARG on at least one clean held-out slice.",
            "transfer_boundary": "No significant harm on a non-STEM or non-formula multiple-choice split.",
            "cost_boundary": "Do not lose to cost-matched plain requery on the claimed positive slice.",
            "claim_boundary": "Keep broad general PromptNode claim disabled unless transfer becomes positive.",
        },
        "current_claim_permissions": claim_permissions,
    }


def build_paper_evidence_summary(
    r313_summary: str = DEFAULT_R313_SUMMARY,
    r319_summary: str = DEFAULT_R319_SUMMARY,
    r320_summary: str = DEFAULT_R320_SUMMARY,
) -> Dict[str, Any]:
    r313 = _load_json(r313_summary)
    r319 = _load_json(r319_summary)
    r320 = _load_json(r320_summary)
    main_results = build_main_results(r313.get("evidence", {}))
    return {
        "run_id": "R321",
        "title": "Paper evidence table and selector-training gate",
        "claim_boundary": (
            "R321 translates the current results into paper-facing tables and freezes the next training gate. It "
            "permits a selector-training preflight, but does not permit training execution yet."
        ),
        "no_api": True,
        "broad_api": False,
        "paper_main_results": main_results,
        "paper_claim_draft": (
            "PromptNode/PromptEdge graph organization improves audited AQuA tail and MMLU STEM while preserving a "
            "no-harm boundary on non-STEM after lifecycle safety replay."
        ),
        "paper_claim_forbidden": [
            "Do not claim universal improvement across all multi-choice tasks.",
            "Do not present warning-only non-STEM nodes as answer-improving nodes.",
            "Do not hide the raw non-STEM negative transfer row.",
        ],
        "ablation_summary": {
            "completed_count": len(r319.get("completed_ablations", [])),
            "priority_pending": r319.get("priority_pending_ablations", []),
            "key_controls": [
                "remove_safety_gate",
                "remove_lifecycle_prune",
                "remove_promptedge_text",
                "remove_symbolic_verifier_family",
                "cost_matched_plain_requery",
            ],
        },
        "selector_training_gate": build_selector_training_gate(r319, r320),
        "next_required_run": "R322_selector_training_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R321 Paper Evidence Table And Training Gate",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Main Results",
        "",
        "| Slice | ARG baseline | PromptNode | Delta | Fix/Harm | Paper Claim |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in summary["paper_main_results"]:
        rows.append(
            f"| `{row['slice']}` | `{row['baseline']}` | `{row['promptnode']}` | `{row['delta_correct']}` | `{row['fix_harm']}` | {row['paper_claim']} |"
        )
    rows.extend(["", "## Training Gate", ""])
    gate = summary["selector_training_gate"]
    rows.append(f"- Preflight authorized: `{gate['preflight_authorized']}`")
    rows.append(f"- Execute training authorized: `{gate['execute_training_authorized']}`")
    rows.append(f"- Allowed target: {gate['allowed_training_target']}")
    rows.extend(["", "## Forbidden Paper Claims", ""])
    rows.extend(f"- {item}" for item in summary["paper_claim_forbidden"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r313_summary: str = DEFAULT_R313_SUMMARY,
    r319_summary: str = DEFAULT_R319_SUMMARY,
    r320_summary: str = DEFAULT_R320_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_paper_evidence_summary(
        r313_summary=r313_summary,
        r319_summary=r319_summary,
        r320_summary=r320_summary,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R321 paper table and selector-training gate.")
    parser.add_argument("--r313_summary", default=DEFAULT_R313_SUMMARY)
    parser.add_argument("--r319_summary", default=DEFAULT_R319_SUMMARY)
    parser.add_argument("--r320_summary", default=DEFAULT_R320_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
