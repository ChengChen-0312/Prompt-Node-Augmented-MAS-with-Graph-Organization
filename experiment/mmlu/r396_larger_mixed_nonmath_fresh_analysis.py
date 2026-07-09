from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R395_RESULTS = "experiment/mmlu/run_logs/mmlu_r395_larger_mixed_nonmath_fresh_api_results.jsonl"
DEFAULT_R395_SUMMARY = "experiment/mmlu/res_logs/mmlu_r395_larger_mixed_nonmath_fresh_api_execution_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_report.md"


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


def _subject_breakdown(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"records": 0, "arg_correct": 0, "hybrid_correct": 0, "fixes": 0, "harms": 0, "wrong_forward": 0})
    for row in rows:
        subject = str(row.get("subject") or "")
        stats[subject]["records"] += 1
        stats[subject]["arg_correct"] += int(bool(row.get("arg_correct")))
        stats[subject]["hybrid_correct"] += int(bool(row.get("final_correct")))
        stats[subject]["fixes"] += int(bool(row.get("fix")))
        stats[subject]["harms"] += int(bool(row.get("harm")))
        stats[subject]["wrong_forward"] += int(bool(row.get("wrong_forward")))
    for subject in stats:
        stats[subject]["delta"] = stats[subject]["hybrid_correct"] - stats[subject]["arg_correct"]
    return dict(sorted(stats.items()))


def build_larger_mixed_analysis(
    r395_results: str = DEFAULT_R395_RESULTS,
    r395_summary: str = DEFAULT_R395_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r395_results)
    r395 = _load_json(r395_summary)
    arg_correct = sum(1 for row in rows if row.get("arg_correct"))
    hybrid_correct = sum(1 for row in rows if row.get("final_correct"))
    fixes = [row for row in rows if row.get("fix")]
    harms = [row for row in rows if row.get("harm")]
    wrong_forward = [row for row in rows if row.get("wrong_forward")]
    missed_fixes = [row for row in rows if not row.get("arg_correct") and not row.get("final_correct") and not row.get("gate_forward")]
    candidate_correct_blocked = [
        row
        for row in rows
        if not row.get("arg_correct")
        and row.get("candidate_label") == row.get("true_answer")
        and not row.get("gate_forward")
    ]
    candidate_types = Counter((row.get("candidate_parsed_response") or {}).get("candidate_type") for row in rows)
    return {
        "run_id": "R396",
        "title": "Larger mixed nonmath fresh analysis and goal audit",
        "claim_boundary": (
            "R396 analyzes R395 and performs the five-iteration goal audit for R391-R395. The larger mixed "
            "nonmath run supports no-harm transfer, but not positive gain."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "arg_correct": arg_correct,
        "hybrid_correct": hybrid_correct,
        "delta_correct": hybrid_correct - arg_correct,
        "arg_accuracy": round(arg_correct / len(rows), 6) if rows else 0.0,
        "hybrid_accuracy": round(hybrid_correct / len(rows), 6) if rows else 0.0,
        "candidate_label_count": sum(1 for row in rows if row.get("candidate_label")),
        "gate_forward_count": sum(1 for row in rows if row.get("gate_forward")),
        "fixes": len(fixes),
        "harms": len(harms),
        "wrong_forward_count": len(wrong_forward),
        "missed_fix_count": len(missed_fixes),
        "candidate_correct_but_blocked_count": len(candidate_correct_blocked),
        "fix_task_ids": [row.get("task_id") for row in fixes],
        "harm_task_ids": [row.get("task_id") for row in harms],
        "wrong_forward_task_ids": [row.get("task_id") for row in wrong_forward],
        "missed_fix_task_ids": [row.get("task_id") for row in missed_fixes],
        "candidate_correct_but_blocked_task_ids": [row.get("task_id") for row in candidate_correct_blocked],
        "subject_breakdown": _subject_breakdown(rows),
        "candidate_type_counts": dict(sorted(candidate_types.items())),
        "iterations_since_last_goal_check": ["R391", "R392", "R393", "R394", "R395"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "larger_mixed_no_harm": not harms,
            "larger_mixed_positive": hybrid_correct > arg_correct and not harms,
            "error_taxonomy_required": True,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "larger_mixed_no_harm_claim_allowed": not harms,
            "positive_mixed_nonmath_claim_allowed": hybrid_correct > arg_correct and not harms,
            "error_taxonomy_allowed_next": True,
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "api_cost": r395.get("api_cost"),
        "prompt_tokens": r395.get("prompt_tokens"),
        "completion_tokens": r395.get("completion_tokens"),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R397_larger_mixed_error_taxonomy",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R396 Larger Mixed Nonmath Fresh Analysis",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- ARG: `{summary['arg_correct']}/{summary['records']}`",
            f"- Hybrid: `{summary['hybrid_correct']}/{summary['records']}`",
            f"- Delta/fix/harm/wrong-forward: `{summary['delta_correct']}/{summary['fixes']}/{summary['harms']}/{summary['wrong_forward_count']}`",
            f"- Candidate-correct blocked: `{summary['candidate_correct_but_blocked_task_ids']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r395_results: str = DEFAULT_R395_RESULTS,
    r395_summary: str = DEFAULT_R395_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_larger_mixed_analysis(r395_results=r395_results, r395_summary=r395_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R395 larger mixed nonmath fresh run.")
    parser.add_argument("--r395_results", default=DEFAULT_R395_RESULTS)
    parser.add_argument("--r395_summary", default=DEFAULT_R395_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
