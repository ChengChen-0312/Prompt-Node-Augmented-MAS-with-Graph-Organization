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


DEFAULT_R376_SUMMARY = "experiment/mmlu/res_logs/mmlu_r376_history_guarded_fresh_eval_analysis_summary.json"
DEFAULT_R377_SUMMARY = "experiment/mmlu/res_logs/mmlu_r377_option_binding_promptedge_replay_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r378_goal_audit_after_option_binding_promptedge_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r378_goal_audit_after_option_binding_promptedge_report.md"


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
    r376_summary: str = DEFAULT_R376_SUMMARY,
    r377_summary: str = DEFAULT_R377_SUMMARY,
) -> Dict[str, Any]:
    r376 = _load_json(r376_summary)
    r377 = _load_json(r377_summary)
    fresh_delta = int(r376.get("delta_correct", 0))
    replay_delta = int(r377.get("delta_vs_arg", 0))
    fresh_harms = int(r376.get("harms", 0))
    replay_harms = int(r377.get("harms", 0))
    return {
        "run_id": "R378",
        "title": "Goal audit after OptionBinding PromptEdge",
        "claim_boundary": (
            "R378 audits R373-R377. The fresh history eval was no-harm but not positive; the OptionBinding "
            "PromptEdge replay is positive but cannot be used as a fresh result. The correct next step is a new "
            "fresh preflight that includes the binding edge from the start."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R373", "R374", "R375", "R376", "R377"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "fresh_history_eval_no_harm": fresh_harms == 0,
            "fresh_history_eval_positive": fresh_delta > 0 and fresh_harms == 0,
            "option_binding_replay_positive": replay_delta > 0 and replay_harms == 0,
            "promptedge_as_first_class_mechanism_supported": r377.get("bound_candidate_count", 0) > 0,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "mechanism_replay_positive_no_harm_allowed": replay_delta > 0 and replay_harms == 0,
            "fresh_preflight_allowed_next": True,
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Do not claim R377 as a main result because it replays R375 outputs.",
            "Build a new fresh manifest where HistoryVerifierPN writes rationale and OptionBindingPromptEdge binds explicit labels before gating.",
            "Keep the R373 learned safety gate; do not relax threshold or use gold labels to bind options.",
            "Evaluate on fresh nonmath/history tasks first, then broaden to mixed nonmath only if the fresh result is positive no-harm.",
        ],
        "evidence_snapshot": {
            "r376_fresh_arg_to_hybrid": f"{r376.get('arg_correct', 0)}/{r376.get('records', 0)} -> {r376.get('hybrid_correct', 0)}/{r376.get('records', 0)}",
            "r376_empty_label_high_confidence": r376.get("empty_candidate_high_confidence_count", 0),
            "r377_replay_arg_to_edge": f"{r377.get('arg_correct', 0)}/{r377.get('records', 0)} -> {r377.get('edge_hybrid_correct', 0)}/{r377.get('records', 0)}",
            "r377_fix_harm_wrong_forward": f"{r377.get('fixes', 0)}/{r377.get('harms', 0)}/{r377.get('wrong_forward_count', 0)}",
        },
        "next_required_run": "R379_option_binding_fresh_eval_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R378 Goal Audit After OptionBinding PromptEdge",
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
    r376_summary: str = DEFAULT_R376_SUMMARY,
    r377_summary: str = DEFAULT_R377_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(r376_summary=r376_summary, r377_summary=r377_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R378 goal audit after OptionBinding PromptEdge replay.")
    parser.add_argument("--r376_summary", default=DEFAULT_R376_SUMMARY)
    parser.add_argument("--r377_summary", default=DEFAULT_R377_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
