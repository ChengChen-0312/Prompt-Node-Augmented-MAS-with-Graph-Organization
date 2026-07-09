from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R342_RESULTS = "experiment/mmlu/run_logs/mmlu_r342_answer_bearing_candidate_generator_api_probe_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r343_answer_bearing_candidate_probe_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r343_answer_bearing_candidate_probe_analysis_report.md"
VALID_LABELS = {"A", "B", "C", "D", "E"}


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


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


def _label(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text[:1] if text[:1] in VALID_LABELS else ""


def _is_executed(row: Dict[str, Any]) -> bool:
    return bool(row.get("api_executed")) and not row.get("api_error")


def build_probe_failure_analysis(r342_results: str = DEFAULT_R342_RESULTS) -> Dict[str, Any]:
    rows = _load_jsonl(r342_results)
    valid = [row for row in rows if _is_executed(row)]
    labels = [row for row in valid if _label(row.get("candidate_label"))]
    follows_wrong_baseline = [
        row
        for row in valid
        if _label(row.get("candidate_label"))
        and _label(row.get("candidate_label")) == _label(row.get("baseline_prediction"))
        and _label(row.get("baseline_prediction")) != _label(row.get("true_answer"))
    ]
    low_evidence = [
        row
        for row in valid
        if int((row.get("parsed_candidate_response") or {}).get("evidence_count") or 0) <= 1
    ]
    root_causes = []
    if len(labels) == len(valid) and not any(row.get("candidate_is_correct") for row in valid):
        root_causes.append("answer_bearing_candidates_not_reliable")
    if follows_wrong_baseline:
        root_causes.append("verifier_candidates_follow_wrong_baseline")
    if len(low_evidence) == len(valid):
        root_causes.append("weak_or_non_executable_evidence")
    root_causes.append("prompt_only_answer_verifiers_not_sufficient")
    task_rows = []
    for row in valid:
        task_rows.append(
            {
                "task_id": row.get("task_id", ""),
                "verifier_family": row.get("verifier_family", ""),
                "baseline_prediction": _label(row.get("baseline_prediction")),
                "candidate_label": _label(row.get("candidate_label")),
                "true_answer": _label(row.get("true_answer")),
                "candidate_is_correct": bool(row.get("candidate_is_correct")),
                "candidate_repairs_baseline": bool(row.get("candidate_repairs_baseline")),
                "evidence_count": int((row.get("parsed_candidate_response") or {}).get("evidence_count") or 0),
            }
        )
    return {
        "run_id": "R343",
        "title": "Answer-bearing candidate probe failure analysis",
        "claim_boundary": (
            "R343 analyzes the executed R342 four-task mechanism probe only. It blocks same-design prompt-only "
            "answer-bearing verifier expansion because every candidate followed the wrong ARG baseline."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "api_executed": len(valid),
        "api_errors": len(rows) - len(valid),
        "candidate_label_count": len(labels),
        "candidate_correct_count": sum(1 for row in valid if row.get("candidate_is_correct")),
        "candidate_repairs_baseline_count": sum(1 for row in valid if row.get("candidate_repairs_baseline")),
        "candidate_harms_baseline_count": sum(1 for row in valid if row.get("candidate_harms_baseline")),
        "candidate_follows_wrong_baseline_count": len(follows_wrong_baseline),
        "verifier_family_counts": dict(sorted(Counter(row.get("verifier_family") for row in valid).items())),
        "root_causes": root_causes,
        "course_correction": [
            "stop_same_prompt_only_verifier_api_expansion",
            "requires_executable_or_symbolic_verification",
            "keep_r342_as_mechanism_debug_not_paper_claim",
            "run_five_iteration_goal_audit_before_next_design",
        ],
        "task_rows": task_rows,
        "claim_permissions": {
            "answer_bearing_generator_improvement_claim_allowed": False,
            "more_api_same_design_allowed": False,
            "tool_verifier_design_required": True,
            "paper_claim_authorized": False,
            "sci_q2_ready": False,
        },
        "next_required_run": "R344_goal_audit_after_candidate_generator_probe",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R343 Answer-Bearing Candidate Probe Failure Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Records: `{summary['records']}`",
        f"- API executed: `{summary['api_executed']}`",
        f"- Candidate labels: `{summary['candidate_label_count']}`",
        f"- Candidate correct: `{summary['candidate_correct_count']}`",
        f"- Candidate repairs: `{summary['candidate_repairs_baseline_count']}`",
        f"- Followed wrong baseline: `{summary['candidate_follows_wrong_baseline_count']}`",
        f"- Root causes: `{summary['root_causes']}`",
        "",
        "## Task Rows",
        "",
    ]
    for row in summary["task_rows"]:
        rows.append(
            "- `{task_id}` `{verifier_family}`: baseline `{baseline_prediction}`, candidate `{candidate_label}`, "
            "gold `{true_answer}`, evidence `{evidence_count}`".format(**row)
        )
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r342_results: str = DEFAULT_R342_RESULTS,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_probe_failure_analysis(r342_results=r342_results)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R342 answer-bearing verifier probe failure.")
    parser.add_argument("--r342_results", default=DEFAULT_R342_RESULTS)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
