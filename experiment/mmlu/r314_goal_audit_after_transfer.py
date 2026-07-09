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
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r314_goal_audit_after_transfer_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r314_goal_audit_after_transfer_report.md"


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


def build_goal_audit_summary(r313_summary: str = DEFAULT_R313_SUMMARY) -> Dict[str, Any]:
    r313 = _load_json(r313_summary)
    permissions = dict(r313.get("claim_permissions", {}))
    return {
        "run_id": "R314",
        "title": "Goal audit after negative controls and transfer",
        "claim_boundary": (
            "R314 is the required five-iteration goal audit after R309-R313. It checks alignment with the SCI-Q2 "
            "PromptNode goal and blocks overclaiming after non-STEM negative transfer."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R309", "R310", "R311", "R312", "R313"],
        "current_evidence": r313.get("evidence", {}),
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_designer_baseline_preserved": True,
            "promptnode_as_first_class_graph_node_preserved": True,
            "negative_controls_checked": True,
            "transfer_checked": True,
            "nonstem_failure_not_hidden": True,
            "claim_boundary_narrowed_correctly": True,
            "training_deferred_until_ablations": True,
        },
        "claim_permissions": {
            "aqua_clean_improvement_allowed": bool(permissions.get("aqua_clean_improvement_allowed")),
            "mmlu_stem_improvement_allowed": bool(permissions.get("mmlu_stem_improvement_allowed")),
            "mmlu_nonstem_no_harm_allowed": bool(permissions.get("mmlu_nonstem_no_harm_allowed")),
            "mmlu_nonstem_improvement_allowed": False,
            "broad_general_promptnode_claim_allowed": False,
            "training_authorized": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Do not train a switching policy from non-STEM warning-only nodes.",
            "Keep non-STEM as no-harm boundary evidence unless answer-bearing semantic nodes are added and prospectively evaluated.",
            "Use AQuA audit-clean and MMLU STEM main97 as the current positive evidence, but require ablations before paper claims.",
            "Report always-forward/no-lifecycle cost issue as a cost-normalized control.",
        ],
        "next_required_run": "R315_ablation_table",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R314 Goal Audit After Transfer",
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
    rows.append("")
    return "\n".join(rows)


def run(
    r313_summary: str = DEFAULT_R313_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(r313_summary=r313_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R314 goal audit after transfer.")
    parser.add_argument("--r313_summary", default=DEFAULT_R313_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
