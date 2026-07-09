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


DEFAULT_R337_SUMMARY = "experiment/mmlu/res_logs/mmlu_r337_prospective_selector_eval_expand24_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r338_goal_audit_after_prospective_eval_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r338_goal_audit_after_prospective_eval_report.md"


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


def build_goal_audit_summary(r337_summary: str = DEFAULT_R337_SUMMARY) -> Dict[str, Any]:
    r337 = _load_json(r337_summary)
    variants = r337.get("by_variant", {})
    arg = variants.get("arg_baseline_direct", {})
    selector = variants.get("selector_promptnode_promptedge_policy", {})
    plain = variants.get("cost_matched_plain_requery", {})
    selector_delta = int(selector.get("correct", 0)) - int(arg.get("correct", 0))
    plain_harms = int(plain.get("harms", 0))
    return {
        "run_id": "R338",
        "title": "Goal audit after prospective selector evaluation",
        "claim_boundary": (
            "R338 is the five-iteration audit after R333-R337. The prospective selector completed a 24-task held-out "
            "smoke, but it tied ARG rather than improving it; therefore prospective improvement remains blocked."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R333", "R334", "R335", "R336", "R337"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "prospective_eval_completed": r337.get("api_executed") is True,
            "api_cost_recorded": r337.get("api_cost") is not None,
            "arg_baseline_preserved": True,
            "overclaiming_blocked": selector_delta <= 0,
        },
        "prospective_result": {
            "arg": f"{arg.get('correct', 0)}/{arg.get('evaluated_records', 0)}",
            "selector": f"{selector.get('correct', 0)}/{selector.get('evaluated_records', 0)}",
            "plain_requery": f"{plain.get('correct', 0)}/{plain.get('evaluated_records', 0)}",
            "selector_delta_correct": selector_delta,
            "selector_fix_harm": f"{selector.get('fixes', 0)}/{selector.get('harms', 0)}",
            "plain_requery_harms": plain_harms,
        },
        "claim_permissions": {
            "prospective_selector_improvement_claim_allowed": selector_delta > 0,
            "prospective_selector_no_harm_claim_allowed": selector_delta == 0 and int(selector.get("harms", 0)) == 0,
            "plain_requery_harm_control_allowed": plain_harms > 0,
            "broad_general_promptnode_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "course_correction": [
            "Analyze why the prospective selector does not switch before spending more API.",
            "Do not expand to 48/full prospective evaluation until a mechanism-level fix is identified.",
            "Keep current paper claims anchored on AQuA audit-clean and MMLU STEM positive evidence.",
            "Use prospective selector as no-harm/cost-control evidence only unless later runs show positive gain.",
        ],
        "next_required_run": "R339_selector_non_switch_failure_analysis",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R338 Goal Audit After Prospective Eval",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Prospective result: `{summary['prospective_result']}`",
        "",
        "## Claim Permissions",
        "",
    ]
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["claim_permissions"].items())
    rows.extend(["", "## Course Correction", ""])
    rows.extend(f"- {item}" for item in summary["course_correction"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r337_summary: str = DEFAULT_R337_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(r337_summary=r337_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R338 goal audit after prospective eval.")
    parser.add_argument("--r337_summary", default=DEFAULT_R337_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
