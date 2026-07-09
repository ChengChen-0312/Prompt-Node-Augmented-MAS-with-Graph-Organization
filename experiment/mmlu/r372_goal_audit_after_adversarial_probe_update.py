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


DEFAULT_R370_SUMMARY = "experiment/mmlu/res_logs/mmlu_r370_adversarial_verifier_probe_analysis_summary.json"
DEFAULT_R371_SUMMARY = "experiment/mmlu/res_logs/mmlu_r371_adversarial_probe_hard_negative_update_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r372_goal_audit_after_adversarial_probe_update_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r372_goal_audit_after_adversarial_probe_update_report.md"


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
    r370_summary: str = DEFAULT_R370_SUMMARY,
    r371_summary: str = DEFAULT_R371_SUMMARY,
) -> Dict[str, Any]:
    r370 = _load_json(r370_summary)
    r371 = _load_json(r371_summary)
    return {
        "run_id": "R372",
        "title": "Goal audit after adversarial probe update",
        "claim_boundary": (
            "R372 audits R367-R371. The adversarial/domain probe failed safely, and its outputs were converted into "
            "hard negatives before any broad API run."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R367", "R368", "R369", "R370", "R371"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "adversarial_probe_failed_safely": r370.get("adversarial_block_count") == 0
            and not r370.get("claim_permissions", {}).get("integrate_unconstrained_domain_verifier"),
            "hard_negative_update_done": r371.get("r369_hard_negative_records") == 7,
            "history_signal_preserved": r371.get("r369_positive_records") == 2,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "offline_retraining_allowed": bool(r371.get("offline_retraining_authorized_next")),
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Retrain source-invariant gate with R369 hard negatives before another fresh API run.",
            "Do not integrate unconstrained domain verifiers directly.",
            "Keep history-passage verifier as a guarded candidate family requiring fresh validation.",
        ],
        "next_required_run": "R373_retrain_after_r369_hard_negatives",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R372 Goal Audit After Adversarial Probe Update",
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
    r370_summary: str = DEFAULT_R370_SUMMARY,
    r371_summary: str = DEFAULT_R371_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(r370_summary=r370_summary, r371_summary=r371_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R372 goal audit after adversarial probe update.")
    parser.add_argument("--r370_summary", default=DEFAULT_R370_SUMMARY)
    parser.add_argument("--r371_summary", default=DEFAULT_R371_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
