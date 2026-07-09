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


DEFAULT_R389_RESULTS = "experiment/mmlu/run_logs/mmlu_r389_mixed_nonmath_option_binding_api_results.jsonl"
DEFAULT_R389_SUMMARY = "experiment/mmlu/res_logs/mmlu_r389_mixed_nonmath_option_binding_api_execution_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r390_mixed_nonmath_option_binding_analysis_and_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r390_mixed_nonmath_option_binding_analysis_and_goal_audit_report.md"


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


def build_mixed_nonmath_analysis(
    r389_results: str = DEFAULT_R389_RESULTS,
    r389_summary: str = DEFAULT_R389_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r389_results)
    r389 = _load_json(r389_summary)
    arg_correct = sum(1 for row in rows if row.get("arg_correct"))
    hybrid_correct = sum(1 for row in rows if row.get("final_correct"))
    fixes = [row for row in rows if row.get("fix")]
    harms = [row for row in rows if row.get("harm")]
    wrong_forward = [row for row in rows if row.get("wrong_forward")]
    missed_fixes = [row for row in rows if not row.get("arg_correct") and not row.get("final_correct") and not row.get("gate_forward")]
    candidate_types = Counter((row.get("candidate_parsed_response") or {}).get("candidate_type") for row in rows)
    return {
        "run_id": "R390",
        "title": "Mixed nonmath OptionBinding analysis and goal audit",
        "claim_boundary": (
            "R390 analyzes R389 and performs the five-iteration goal audit for R385-R389. Mixed nonmath transfer "
            "is positive no-harm but small, and wrong-forward hard negatives must be added before scaling."
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
        "fix_task_ids": [row.get("task_id") for row in fixes],
        "harm_task_ids": [row.get("task_id") for row in harms],
        "wrong_forward_task_ids": [row.get("task_id") for row in wrong_forward],
        "missed_fix_task_ids": [row.get("task_id") for row in missed_fixes],
        "subject_breakdown": _subject_breakdown(rows),
        "candidate_type_counts": dict(sorted(candidate_types.items())),
        "iterations_since_last_goal_check": ["R385", "R386", "R387", "R388", "R389"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "mixed_nonmath_positive_no_harm": hybrid_correct > arg_correct and not harms,
            "gain_insufficient_for_sci_q2": (hybrid_correct - arg_correct) < 3,
            "hard_negative_update_required": bool(wrong_forward),
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "mixed_nonmath_small_positive_no_harm_claim_allowed": hybrid_correct > arg_correct and not harms,
            "hard_negative_update_allowed_next": True,
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "api_cost": r389.get("api_cost"),
        "prompt_tokens": r389.get("prompt_tokens"),
        "completion_tokens": r389.get("completion_tokens"),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R391_mixed_nonmath_hard_negative_update",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R390 Mixed Nonmath OptionBinding Analysis And Goal Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- ARG: `{summary['arg_correct']}/{summary['records']}`",
        f"- Hybrid: `{summary['hybrid_correct']}/{summary['records']}`",
        f"- Delta/fix/harm/wrong-forward: `{summary['delta_correct']}/{summary['fixes']}/{summary['harms']}/{summary['wrong_forward_count']}`",
        f"- Fix tasks: `{summary['fix_task_ids']}`",
        f"- Wrong-forward tasks: `{summary['wrong_forward_task_ids']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run(
    r389_results: str = DEFAULT_R389_RESULTS,
    r389_summary: str = DEFAULT_R389_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_mixed_nonmath_analysis(r389_results=r389_results, r389_summary=r389_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R389 mixed nonmath OptionBinding and audit goal alignment.")
    parser.add_argument("--r389_results", default=DEFAULT_R389_RESULTS)
    parser.add_argument("--r389_summary", default=DEFAULT_R389_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
