from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R395_RESULTS = "experiment/mmlu/run_logs/mmlu_r395_larger_mixed_nonmath_fresh_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r397_larger_mixed_error_taxonomy_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r397_larger_mixed_error_taxonomy_report.md"


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


def build_error_taxonomy(r395_results: str = DEFAULT_R395_RESULTS) -> Dict[str, Any]:
    rows = _load_jsonl(r395_results)
    wrong_forward = [row for row in rows if row.get("wrong_forward")]
    missed = [row for row in rows if not row.get("arg_correct") and not row.get("final_correct") and not row.get("gate_forward")]
    candidate_correct_blocked = [
        row
        for row in missed
        if row.get("candidate_label") and row.get("candidate_label") == row.get("true_answer")
    ]
    abstentions = [row for row in missed if not row.get("candidate_label")]
    candidate_wrong_missed = [row for row in missed if row.get("candidate_label") and row.get("candidate_label") != row.get("true_answer")]
    root_causes = [
        "wrong_forward_definition_misbinding",
        "candidate_quality_failure",
        "gate_over_pruning_for_candidate_type_option",
        "abstention_or_schema_failure",
    ]
    return {
        "run_id": "R397",
        "title": "Larger mixed error taxonomy",
        "claim_boundary": (
            "R397 classifies R395 errors. It is diagnostic only and cannot support a paper claim by itself."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "wrong_forward_count": len(wrong_forward),
        "missed_fix_count": len(missed),
        "candidate_correct_but_blocked_count": len(candidate_correct_blocked),
        "abstention_or_schema_failure_count": len(abstentions),
        "candidate_wrong_missed_count": len(candidate_wrong_missed),
        "wrong_forward_task_ids": [row.get("task_id") for row in wrong_forward],
        "candidate_correct_but_blocked_task_ids": [row.get("task_id") for row in candidate_correct_blocked],
        "abstention_task_ids": [row.get("task_id") for row in abstentions],
        "candidate_wrong_missed_task_ids": [row.get("task_id") for row in candidate_wrong_missed],
        "root_causes": root_causes,
        "method_implications": [
            "Add a contrastive option-verification PromptNode that must explicitly reject the nearest distractor before forwarding.",
            "Add a concept-definition anchor PromptNode for philosophy, moral, and logical-fallacy questions.",
            "Use PromptEdge evidence to distinguish direct option binding from generic semantic plausibility.",
            "Keep the weighted gate conservative until a fresh positive delta reappears.",
        ],
        "claim_permissions": {
            "design_iteration_allowed_next": True,
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R398_nonmath_contrastive_verifier_design",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R397 Larger Mixed Error Taxonomy",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Wrong-forward: `{summary['wrong_forward_count']}`",
        f"- Missed fixes: `{summary['missed_fix_count']}`",
        f"- Candidate-correct blocked: `{summary['candidate_correct_but_blocked_count']}`",
        f"- Root causes: `{summary['root_causes']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run(
    r395_results: str = DEFAULT_R395_RESULTS,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_error_taxonomy(r395_results=r395_results)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify R395 larger mixed errors.")
    parser.add_argument("--r395_results", default=DEFAULT_R395_RESULTS)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
