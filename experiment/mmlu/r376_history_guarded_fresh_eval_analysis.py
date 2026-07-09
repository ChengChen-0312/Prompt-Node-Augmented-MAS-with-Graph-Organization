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
from experiment.mmlu.r375_history_guarded_fresh_eval_api_execution import _confidence_value


DEFAULT_R375_RESULTS = "experiment/mmlu/run_logs/mmlu_r375_history_guarded_fresh_eval_api_results.jsonl"
DEFAULT_R375_SUMMARY = "experiment/mmlu/res_logs/mmlu_r375_history_guarded_fresh_eval_api_execution_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r376_history_guarded_fresh_eval_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r376_history_guarded_fresh_eval_analysis_report.md"


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


def _explicit_option_labels(rationale: str) -> List[str]:
    labels = []
    for match in re.finditer(r"\bOption\s+([A-E])\b", str(rationale or ""), flags=re.I):
        labels.append(_label(match.group(1)))
    return [label for label in labels if label]


def _candidate(row: Dict[str, Any]) -> Dict[str, Any]:
    parsed = row.get("candidate_parsed_response") or {}
    return parsed if isinstance(parsed, dict) else {}


def _hidden_signal(row: Dict[str, Any]) -> bool:
    parsed = _candidate(row)
    return (
        not _label(row.get("candidate_label"))
        and _confidence_value(parsed.get("confidence")) >= 0.85
        and int(parsed.get("evidence_count") or 0) >= 1
        and bool(str(parsed.get("rationale") or "").strip())
    )


def build_history_guarded_analysis(
    r375_results: str = DEFAULT_R375_RESULTS,
    r375_summary: str = DEFAULT_R375_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r375_results)
    r375 = _load_json(r375_summary)
    arg_correct = sum(1 for row in rows if row.get("arg_correct"))
    hybrid_correct = sum(1 for row in rows if row.get("final_correct"))
    forwarded = [row for row in rows if row.get("gate_forward")]
    fixes = [row for row in rows if row.get("fix")]
    harms = [row for row in rows if row.get("harm")]
    wrong_forward = [row for row in forwarded if not row.get("final_correct")]
    missed_fixes = [row for row in rows if not row.get("arg_correct") and not row.get("final_correct") and not row.get("gate_forward")]
    hidden_rows = [row for row in rows if _hidden_signal(row)]
    hidden_missed = [row for row in missed_fixes if _hidden_signal(row)]
    explicit_true = []
    for row in hidden_rows:
        labels = _explicit_option_labels((_candidate(row)).get("rationale", ""))
        if _label(row.get("true_answer")) in labels:
            explicit_true.append(row)
    return {
        "run_id": "R376",
        "title": "History-guarded fresh eval analysis",
        "claim_boundary": (
            "R376 analyzes R375. It supports no-harm on this fresh history subset, but no positive delta. "
            "The main bottleneck is candidate-to-edge option binding: the PromptNode often wrote a high-confidence "
            "rationale while leaving candidate_label empty."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "arg_correct": arg_correct,
        "hybrid_correct": hybrid_correct,
        "delta_correct": hybrid_correct - arg_correct,
        "arg_accuracy": round(arg_correct / len(rows), 6) if rows else 0.0,
        "hybrid_accuracy": round(hybrid_correct / len(rows), 6) if rows else 0.0,
        "gate_forward_count": len(forwarded),
        "fixes": len(fixes),
        "harms": len(harms),
        "wrong_forward_count": len(wrong_forward),
        "missed_fix_count": len(missed_fixes),
        "empty_candidate_high_confidence_count": len(hidden_rows),
        "empty_candidate_high_confidence_missed_fix_count": len(hidden_missed),
        "empty_candidate_explicit_true_option_count": len(explicit_true),
        "fix_task_ids": [row.get("task_id") for row in fixes],
        "harm_task_ids": [row.get("task_id") for row in harms],
        "wrong_forward_task_ids": [row.get("task_id") for row in wrong_forward],
        "missed_fix_task_ids": [row.get("task_id") for row in missed_fixes],
        "option_binding_bottleneck_task_ids": [row.get("task_id") for row in hidden_missed],
        "explicit_true_option_task_ids": [row.get("task_id") for row in explicit_true],
        "api_cost": r375.get("api_cost"),
        "prompt_tokens": r375.get("prompt_tokens"),
        "completion_tokens": r375.get("completion_tokens"),
        "claim_permissions": {
            "fresh_no_harm_claim_allowed": not harms,
            "fresh_positive_delta_claim_allowed": hybrid_correct > arg_correct and not harms,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R377_option_binding_promptedge_replay",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R376 History-Guarded Fresh Eval Analysis",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- ARG: `{summary['arg_correct']}/{summary['records']}`",
            f"- Hybrid: `{summary['hybrid_correct']}/{summary['records']}`",
            f"- Delta correct: `{summary['delta_correct']}`",
            f"- Gate forward/fix/harm/wrong-forward: `{summary['gate_forward_count']}/{summary['fixes']}/{summary['harms']}/{summary['wrong_forward_count']}`",
            f"- Empty-label high-confidence rationales: `{summary['empty_candidate_high_confidence_count']}`",
            f"- Option-binding bottleneck tasks: `{summary['option_binding_bottleneck_task_ids']}`",
            f"- Explicit true-option rationale tasks: `{summary['explicit_true_option_task_ids']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r375_results: str = DEFAULT_R375_RESULTS,
    r375_summary: str = DEFAULT_R375_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_history_guarded_analysis(r375_results=r375_results, r375_summary=r375_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R375 history-guarded fresh eval.")
    parser.add_argument("--r375_results", default=DEFAULT_R375_RESULTS)
    parser.add_argument("--r375_summary", default=DEFAULT_R375_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
