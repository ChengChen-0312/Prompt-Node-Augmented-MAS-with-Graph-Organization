from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_R264_SUMMARY = os.path.join(SCRIPT_DIR, "res_logs", "aqua_r264_strong_teacher_summary.json")
DEFAULT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "res_logs", "aqua_r265_goal_audit_after_r264_summary.json")
DEFAULT_REPORT_MD = os.path.join(SCRIPT_DIR, "run_logs", "aqua_r265_goal_audit_after_r264.md")


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def build_goal_audit_summary(r264: Dict[str, Any]) -> Dict[str, Any]:
    teacher_improved = r264.get("oracle_teacher_accuracy") not in {"31/34", None}
    leakage_ok = bool(r264.get("leakage_pass")) and int(r264.get("api_errors") or 0) == 0
    disagreement_flags = list(r264.get("dataset_disagreement_flags") or [])
    return {
        "run_id": "R265",
        "title": "Five-iteration SCI-Q2 goal audit after R264",
        "audit_window": "R261-R264",
        "status": "aligned_redirect_to_label_noise_and_low_cost_selector",
        "drift": False,
        "sci_q2_ready": False,
        "r264_teacher_improved": teacher_improved,
        "r264_leakage_ok": leakage_ok,
        "r264_oracle_teacher_accuracy": r264.get("oracle_teacher_accuracy"),
        "r264_non_oracle_teacher_accuracy": r264.get("non_oracle_teacher_accuracy"),
        "dataset_disagreement_flags": disagreement_flags,
        "aligned_evidence": [
            "R262 keeps R065 as an expensive teacher rather than deployment method.",
            "R263 keeps distillation as a low-cost selector scaffold only.",
            "R264 tests stronger general PromptNode/PromptEdge verifiers without exposing gold labels.",
            "R264 refuses to optimize toward target-specific formulas when verifiers consistently oppose dataset labels.",
        ],
        "blocked_claims": [
            "do_not_distill_r264_as_higher_teacher",
            "do_not_claim_32_34_plus_aqua_teacher",
            "do_not_treat_remaining_r065_errors_as_clean_fix_targets_without_label_audit",
            "do_not_expand_task_specific_prompt_formulas",
        ],
        "next_actions": [
            "Run a label-noise/error-boundary audit for task_59/task_139/task_228 and mark them outside clean improvement claims if confirmed noisy.",
            "Resume R263-style low-cost selector distillation from R065's already supported fixes, not from R264's failed higher-teacher targets.",
            "Keep SCI-Q2 claim centered on robust PromptNode graph organization, clean fix/harm, controls, lifecycle, and cost boundary.",
            "Next mandatory goal audit is R270.",
        ],
        "claim_boundary": (
            "Aligned with the SCI-Q2 goal, but not paper-ready. R264 is negative evidence against "
            "unbounded strong-teacher expansion on the remaining R065 errors."
        ),
    }


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# R265 Goal Audit After R264",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Audit window: `{summary['audit_window']}`",
        f"- Status: `{summary['status']}`",
        f"- Drift: `{summary['drift']}`",
        f"- SCI-Q2 ready: `{summary['sci_q2_ready']}`",
        f"- R264 teacher improved: `{summary['r264_teacher_improved']}`",
        f"- R264 oracle/non-oracle: `{summary['r264_oracle_teacher_accuracy']}` / `{summary['r264_non_oracle_teacher_accuracy']}`",
        f"- R264 leakage OK: `{summary['r264_leakage_ok']}`",
        f"- Dataset-disagreement flags: `{', '.join(summary['dataset_disagreement_flags']) or 'none'}`",
        "",
        "## Aligned Evidence",
        "",
    ]
    lines.extend(f"- {item}" for item in summary["aligned_evidence"])
    lines.extend(["", "## Blocked Claims", ""])
    lines.extend(f"- `{item}`" for item in summary["blocked_claims"])
    lines.extend(["", "## Next Actions", ""])
    lines.extend(f"- {item}" for item in summary["next_actions"])
    lines.append("")
    return "\n".join(lines)


def run_goal_audit(r264_summary: str, summary_json: str, report_md: str) -> Dict[str, Any]:
    summary = build_goal_audit_summary(load_json(r264_summary))
    write_json(summary_json, summary)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R265 goal audit after R264.")
    parser.add_argument("--r264_summary", default=DEFAULT_R264_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_goal_audit(args.r264_summary, args.summary_json, args.report_md)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
