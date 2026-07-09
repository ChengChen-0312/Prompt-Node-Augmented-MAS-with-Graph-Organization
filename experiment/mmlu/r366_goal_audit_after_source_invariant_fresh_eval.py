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


DEFAULT_R364_SUMMARY = "experiment/mmlu/res_logs/mmlu_r364_source_invariant_fresh_eval_analysis_summary.json"
DEFAULT_R365_SUMMARY = "experiment/mmlu/res_logs/mmlu_r365_wrong_forward_and_missed_fix_analysis_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r366_goal_audit_after_source_invariant_fresh_eval_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r366_goal_audit_after_source_invariant_fresh_eval_report.md"


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


def build_goal_audit_summary(
    r364_summary: str = DEFAULT_R364_SUMMARY,
    r365_summary: str = DEFAULT_R365_SUMMARY,
) -> Dict[str, Any]:
    r364 = _load_json(r364_summary)
    r365 = _load_json(r365_summary)
    delta = int(r364.get("delta_correct", 0))
    harms = int(r364.get("harms", 0))
    return {
        "run_id": "R366",
        "title": "Goal audit after source-invariant fresh eval",
        "claim_boundary": (
            "R366 audits the R362-R365 fresh evaluation cycle. The source-invariant policy has a real no-harm "
            "positive delta, but the gain is too small for an SCI-Q2 main claim."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R362", "R363", "R364", "R365"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "fresh_eval_positive_no_harm": delta > 0 and harms == 0,
            "gain_insufficient_for_sci_q2": delta < 3,
            "candidate_quality_bottleneck_identified": "candidate_quality_not_gate_threshold_is_primary_bottleneck"
            in r365.get("root_causes", []),
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "fresh_positive_delta_no_harm_claim_allowed": delta > 0 and harms == 0,
            "api_execution_allowed_now": False,
            "candidate_quality_iteration_allowed": True,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Improve candidate quality with adversarial and domain-specific verifier edges before another API run.",
            "Keep source-invariant gate and conservative threshold; do not relax gate to chase coverage.",
            "Use R363/R365 as fresh evidence and diagnostic data, not as final main-result evidence.",
        ],
        "evidence_snapshot": {
            "r364_arg_vs_hybrid": f"{r364.get('arg_correct', 0)}/{r364.get('records', 0)} -> {r364.get('hybrid_correct', 0)}/{r364.get('records', 0)}",
            "r364_fix_harm": f"{r364.get('fixes', 0)}/{r364.get('harms', 0)}",
            "r365_wrong_forward_count": r365.get("wrong_forward_count", 0),
            "r365_missed_fix_count": r365.get("missed_fix_count", 0),
        },
        "next_required_run": "R367_adversarial_candidate_verifier_design",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R366 Goal Audit After Source-Invariant Fresh Eval",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Alignment",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", "## Course Correction", ""])
    rows.extend(f"- {item}" for item in summary["course_correction"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r364_summary: str = DEFAULT_R364_SUMMARY,
    r365_summary: str = DEFAULT_R365_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(r364_summary=r364_summary, r365_summary=r365_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R366 goal audit after source-invariant fresh eval.")
    parser.add_argument("--r364_summary", default=DEFAULT_R364_SUMMARY)
    parser.add_argument("--r365_summary", default=DEFAULT_R365_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
