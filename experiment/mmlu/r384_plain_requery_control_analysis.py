from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r335_prospective_selector_eval_api_smoke import _label


DEFAULT_R383_RESULTS = "experiment/mmlu/run_logs/mmlu_r383_plain_requery_control_api_results.jsonl"
DEFAULT_R383_SUMMARY = "experiment/mmlu/res_logs/mmlu_r383_plain_requery_control_api_execution_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r384_plain_requery_control_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r384_plain_requery_control_analysis_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    p = _repo_path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _explicit_option_fallback(row: Dict[str, Any]) -> str:
    prediction = _label(row.get("plain_prediction"))
    if prediction:
        return prediction
    rationale = (row.get("parsed_response") or {}).get("rationale", "")
    labels = sorted(set(_label(match.group(1)) for match in re.finditer(r"\bOption\s+([A-E])\b", str(rationale), flags=re.I)))
    labels = [label for label in labels if label]
    return labels[0] if len(labels) == 1 else ""


def build_plain_requery_control_analysis(
    r383_results: str = DEFAULT_R383_RESULTS,
    r383_summary: str = DEFAULT_R383_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r383_results)
    r383 = _load_json(r383_summary)
    plain_empty = [row for row in rows if not _label(row.get("plain_prediction"))]
    fallback_predictions = {row.get("task_id"): _explicit_option_fallback(row) for row in rows}
    plain_fallback_correct = sum(1 for row in rows if fallback_predictions.get(row.get("task_id")) == _label(row.get("true_answer")))
    arg_correct = sum(1 for row in rows if row.get("r380_arg_correct"))
    plain_strict_correct = sum(1 for row in rows if row.get("plain_correct"))
    option_binding_correct = sum(1 for row in rows if row.get("r380_option_binding_correct"))
    return {
        "run_id": "R384",
        "title": "Plain requery control analysis and goal audit",
        "claim_boundary": (
            "R384 analyzes R383 and performs the five-iteration goal audit for R379-R383. The current plain "
            "control is informative but not decisive because strict scoring penalizes empty selected_label fields "
            "even when the rationale sometimes names the option."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "arg_correct": arg_correct,
        "plain_strict_correct": plain_strict_correct,
        "plain_explicit_fallback_correct": plain_fallback_correct,
        "option_binding_correct": option_binding_correct,
        "plain_empty_label_count": len(plain_empty),
        "option_binding_delta_vs_plain_strict": option_binding_correct - plain_strict_correct,
        "option_binding_delta_vs_plain_fallback": option_binding_correct - plain_fallback_correct,
        "plain_strict_fix_task_ids": r383.get("plain_fix_task_ids", []),
        "plain_empty_label_task_ids": [row.get("task_id") for row in plain_empty],
        "option_binding_only_vs_fallback_task_ids": [
            row.get("task_id")
            for row in rows
            if row.get("r380_option_binding_correct") and fallback_predictions.get(row.get("task_id")) != _label(row.get("true_answer"))
        ],
        "control_validity": {
            "strict_control_underestimates_plain": len(plain_empty) > 0,
            "explicit_fallback_still_below_option_binding": option_binding_correct > plain_fallback_correct,
            "equal_contract_control_required": True,
        },
        "iterations_since_last_goal_check": ["R379", "R380", "R381", "R382", "R383"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "fresh_option_binding_positive_no_harm": option_binding_correct > arg_correct,
            "plain_control_incomplete": len(plain_empty) > 0,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "fresh_positive_delta_no_harm_claim_allowed": option_binding_correct > arg_correct,
            "equal_contract_control_preflight_allowed_next": True,
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "api_cost": r383.get("api_cost"),
        "prompt_tokens": r383.get("prompt_tokens"),
        "completion_tokens": r383.get("completion_tokens"),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R385_equal_contract_plain_control_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R384 Plain Requery Control Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- ARG/plain strict/plain fallback/OptionBinding: `{summary['arg_correct']}/{summary['plain_strict_correct']}/{summary['plain_explicit_fallback_correct']}/{summary['option_binding_correct']}`",
        f"- Plain empty labels: `{summary['plain_empty_label_count']}`",
        f"- OptionBinding delta vs plain strict/fallback: `{summary['option_binding_delta_vs_plain_strict']}/{summary['option_binding_delta_vs_plain_fallback']}`",
        f"- Equal-contract control required: `{summary['control_validity']['equal_contract_control_required']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run(
    r383_results: str = DEFAULT_R383_RESULTS,
    r383_summary: str = DEFAULT_R383_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_plain_requery_control_analysis(r383_results=r383_results, r383_summary=r383_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R383 plain requery control and audit goal alignment.")
    parser.add_argument("--r383_results", default=DEFAULT_R383_RESULTS)
    parser.add_argument("--r383_summary", default=DEFAULT_R383_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
