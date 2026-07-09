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


DEFAULT_R363_RESULTS = "experiment/mmlu/run_logs/mmlu_r363_source_invariant_fresh_eval_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r365_wrong_forward_and_missed_fix_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r365_wrong_forward_and_missed_fix_analysis_report.md"


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


def build_error_analysis(r363_results: str = DEFAULT_R363_RESULTS) -> Dict[str, Any]:
    rows = _load_jsonl(r363_results)
    wrong_forward = [row for row in rows if row.get("gate_forward") and not row.get("final_correct")]
    missed_fix = [row for row in rows if not row.get("arg_correct") and not row.get("final_correct") and not row.get("gate_forward")]
    missed_subject_counts = Counter(row.get("subject") for row in missed_fix)
    root_causes = []
    if wrong_forward:
        root_causes.append("candidate_quality_not_gate_threshold_is_primary_bottleneck")
        root_causes.append("single_candidate_forward_lacks_adversarial_verification")
    if missed_subject_counts.get("college_chemistry", 0) + missed_subject_counts.get("high_school_physics", 0) > 0:
        root_causes.append("chemistry_and_physics_specialized_verifiers_missing")
    if missed_subject_counts.get("high_school_us_history", 0) > 0:
        root_causes.append("passage_history_entailment_verifier_too_weak")
    return {
        "run_id": "R365",
        "title": "Wrong-forward and missed-fix analysis",
        "claim_boundary": (
            "R365 diagnoses why R363 gains only one item. It does not authorize more API; it identifies candidate "
            "quality and missing verifier families as the next bottlenecks."
        ),
        "no_api": True,
        "broad_api": False,
        "wrong_forward_count": len(wrong_forward),
        "wrong_forward_task_ids": [row.get("task_id") for row in wrong_forward],
        "wrong_forward_subject_counts": dict(sorted(Counter(row.get("subject") for row in wrong_forward).items())),
        "missed_fix_count": len(missed_fix),
        "missed_fix_task_ids": [row.get("task_id") for row in missed_fix],
        "missed_fix_subject_counts": dict(sorted(missed_subject_counts.items())),
        "root_causes": root_causes,
        "recommended_next_design": [
            "Add adversarial verifier edge for high-confidence single-candidate forwards.",
            "Add chemistry/physics verifier candidates with stricter evidence contracts.",
            "Add passage-entailment verifier for history tasks with quoted source text.",
            "Keep R360 gate threshold conservative; improve candidate generation before relaxing it.",
        ],
        "api_execution_authorized_next": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R366_goal_audit_after_source_invariant_fresh_eval",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R365 Wrong-Forward And Missed-Fix Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Wrong forwards: `{summary['wrong_forward_count']}` `{summary['wrong_forward_task_ids']}`",
        f"- Missed fixes: `{summary['missed_fix_count']}`",
        f"- Missed-fix subjects: `{summary['missed_fix_subject_counts']}`",
        f"- Root causes: `{summary['root_causes']}`",
        "",
        "## Recommended Next Design",
        "",
    ]
    rows.extend(f"- {item}" for item in summary["recommended_next_design"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r363_results: str = DEFAULT_R363_RESULTS,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_error_analysis(r363_results=r363_results)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R363 wrong forwards and missed fixes.")
    parser.add_argument("--r363_results", default=DEFAULT_R363_RESULTS)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
