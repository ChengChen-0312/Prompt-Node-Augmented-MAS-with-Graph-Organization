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


DEFAULT_R386_RESULTS = "experiment/mmlu/run_logs/mmlu_r386_equal_contract_plain_control_api_results.jsonl"
DEFAULT_R386_SUMMARY = "experiment/mmlu/res_logs/mmlu_r386_equal_contract_plain_control_api_execution_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r387_equal_contract_plain_control_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r387_equal_contract_plain_control_analysis_report.md"


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
    prediction = _label(row.get("equal_contract_prediction"))
    if prediction:
        return prediction
    rationale = (row.get("parsed_response") or {}).get("rationale", "")
    labels = sorted(set(_label(match.group(1)) for match in re.finditer(r"\bOption\s+([A-E])\b", str(rationale), flags=re.I)))
    labels = [label for label in labels if label]
    return labels[0] if len(labels) == 1 else ""


def build_equal_contract_analysis(
    r386_results: str = DEFAULT_R386_RESULTS,
    r386_summary: str = DEFAULT_R386_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r386_results)
    r386 = _load_json(r386_summary)
    fallback_predictions = {row.get("task_id"): _explicit_option_fallback(row) for row in rows}
    arg_correct = sum(1 for row in rows if row.get("r380_arg_correct"))
    strict_correct = sum(1 for row in rows if row.get("equal_contract_correct"))
    fallback_correct = sum(1 for row in rows if fallback_predictions.get(row.get("task_id")) == _label(row.get("true_answer")))
    option_binding_correct = sum(1 for row in rows if row.get("r380_option_binding_correct"))
    empty_rows = [row for row in rows if not _label(row.get("equal_contract_prediction"))]
    return {
        "run_id": "R387",
        "title": "Equal-contract plain control analysis",
        "claim_boundary": (
            "R387 analyzes R386. R380's PromptEdge graph path remains better than a same-task plain prompt with "
            "the same structured output contract, mainly because the plain control often fails to bind a label."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "arg_correct": arg_correct,
        "equal_contract_strict_correct": strict_correct,
        "equal_contract_explicit_fallback_correct": fallback_correct,
        "option_binding_correct": option_binding_correct,
        "equal_contract_empty_label_count": len(empty_rows),
        "option_binding_delta_vs_equal_contract_strict": option_binding_correct - strict_correct,
        "option_binding_delta_vs_equal_contract_fallback": option_binding_correct - fallback_correct,
        "equal_contract_empty_label_task_ids": [row.get("task_id") for row in empty_rows],
        "option_binding_only_vs_equal_contract_fallback_task_ids": [
            row.get("task_id")
            for row in rows
            if row.get("r380_option_binding_correct") and fallback_predictions.get(row.get("task_id")) != _label(row.get("true_answer"))
        ],
        "claim_permissions": {
            "same_task_control_survived": option_binding_correct > fallback_correct,
            "mixed_nonmath_preflight_allowed_next": True,
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "claim_risks": {
            "same_task_control_not_independent_fresh_split": True,
            "history_subject_only": True,
            "needs_mixed_nonmath_transfer": True,
        },
        "api_cost": r386.get("api_cost"),
        "prompt_tokens": r386.get("prompt_tokens"),
        "completion_tokens": r386.get("completion_tokens"),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R388_mixed_nonmath_option_binding_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R387 Equal-Contract Plain Control Analysis",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- ARG/equal strict/equal fallback/OptionBinding: `{summary['arg_correct']}/{summary['equal_contract_strict_correct']}/{summary['equal_contract_explicit_fallback_correct']}/{summary['option_binding_correct']}`",
            f"- Equal-contract empty labels: `{summary['equal_contract_empty_label_count']}`",
            f"- OptionBinding delta vs equal fallback: `{summary['option_binding_delta_vs_equal_contract_fallback']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r386_results: str = DEFAULT_R386_RESULTS,
    r386_summary: str = DEFAULT_R386_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_equal_contract_analysis(r386_results=r386_results, r386_summary=r386_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R386 equal-contract plain control.")
    parser.add_argument("--r386_results", default=DEFAULT_R386_RESULTS)
    parser.add_argument("--r386_summary", default=DEFAULT_R386_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
