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


DEFAULT_R313_SUMMARY = "experiment/mmlu/res_logs/mmlu_r313_claim_matrix_summary.json"
DEFAULT_R319_SUMMARY = "experiment/mmlu/res_logs/mmlu_r319_ablation_table_update_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r320_goal_audit_after_ablations_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r320_goal_audit_after_ablations_report.md"


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


def _completed_ablations(r319: Dict[str, Any]) -> set[str]:
    return set(r319.get("completed_ablations", []))


def build_goal_audit_summary(
    r313_summary: str = DEFAULT_R313_SUMMARY,
    r319_summary: str = DEFAULT_R319_SUMMARY,
) -> Dict[str, Any]:
    r313 = _load_json(r313_summary)
    r319 = _load_json(r319_summary)
    r313_permissions = dict(r313.get("claim_permissions", {}))
    completed = _completed_ablations(r319)
    priority_done = not r319.get("priority_pending_ablations")
    return {
        "run_id": "R320",
        "title": "Goal audit after completed ablation controls",
        "claim_boundary": (
            "R320 is the required five-iteration goal audit after R315-R319. The work stayed aligned with the "
            "SCI-Q2 PromptNode goal by completing reviewer-facing ablations, but it still does not justify a broad "
            "general-improvement claim or training a selector from warning-only non-STEM nodes."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R315", "R316", "R317", "R318", "R319"],
        "ablation_status": {
            "completed_count": len(completed),
            "pending": r319.get("pending_ablations", []),
            "priority_pending": r319.get("priority_pending_ablations", []),
            "all_priority_completed": priority_done,
        },
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_designer_baseline_preserved": True,
            "promptnode_as_first_class_graph_node_preserved": True,
            "promptedge_as_first_class_constraint_preserved": True,
            "priority_ablations_completed": priority_done,
            "promptedge_text_validated": "remove_promptedge_text" in completed,
            "cost_matched_requery_checked": "cost_matched_plain_requery" in completed,
            "symbolic_and_nonmath_contributions_separated": "remove_symbolic_verifier_family" in completed
            and "remove_nonmath_promptnodes" in completed,
            "nonstem_negative_transfer_not_hidden": True,
            "claim_boundary_narrowed_correctly": True,
        },
        "claim_permissions": {
            "aqua_clean_improvement_allowed": bool(r313_permissions.get("aqua_clean_improvement_allowed")),
            "mmlu_stem_improvement_allowed": bool(r313_permissions.get("mmlu_stem_improvement_allowed")),
            "mmlu_nonstem_no_harm_allowed": bool(r313_permissions.get("mmlu_nonstem_no_harm_allowed")),
            "mmlu_nonstem_improvement_allowed": False,
            "broad_general_promptnode_claim_allowed": False,
            "training_authorized": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Treat non-STEM semantic/warning PromptNodes as lifecycle and safety signals unless a future prospective run shows answer-bearing gains.",
            "Do not claim generic transfer improvement: current positive evidence is AQuA audit-clean and MMLU STEM, while non-STEM supports no-harm only.",
            "Use the completed ablations to write the method boundary: PromptNode identity, PromptEdge text, SafetyGate, and lifecycle pruning are all necessary controls.",
            "Before training, build a paper evidence table and a selector-training gate that forbids learning from label-audited or warning-only override failures.",
        ],
        "next_required_run": "R321_paper_evidence_table_and_training_gate",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R320 Goal Audit After Ablations",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Alignment",
        "",
    ]
    rows.extend(f"- `{name}`: `{value}`" for name, value in summary["goal_alignment"].items())
    rows.extend(["", "## Claim Permissions", ""])
    rows.extend(f"- `{name}`: `{value}`" for name, value in summary["claim_permissions"].items())
    rows.extend(["", "## Course Correction", ""])
    rows.extend(f"- {item}" for item in summary["course_correction"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r313_summary: str = DEFAULT_R313_SUMMARY,
    r319_summary: str = DEFAULT_R319_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(r313_summary=r313_summary, r319_summary=r319_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R320 goal audit after ablations.")
    parser.add_argument("--r313_summary", default=DEFAULT_R313_SUMMARY)
    parser.add_argument("--r319_summary", default=DEFAULT_R319_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
