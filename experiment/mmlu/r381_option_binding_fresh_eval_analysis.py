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


DEFAULT_R380_RESULTS = "experiment/mmlu/run_logs/mmlu_r380_option_binding_fresh_eval_api_results.jsonl"
DEFAULT_R380_SUMMARY = "experiment/mmlu/res_logs/mmlu_r380_option_binding_fresh_eval_api_execution_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r381_option_binding_fresh_eval_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r381_option_binding_fresh_eval_analysis_report.md"


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


def build_option_binding_fresh_analysis(
    r380_results: str = DEFAULT_R380_RESULTS,
    r380_summary: str = DEFAULT_R380_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r380_results)
    r380 = _load_json(r380_summary)
    arg_correct = sum(1 for row in rows if row.get("arg_correct"))
    hybrid_correct = sum(1 for row in rows if row.get("final_correct"))
    fixes = [row for row in rows if row.get("fix")]
    harms = [row for row in rows if row.get("harm")]
    wrong_forward = [row for row in rows if row.get("wrong_forward")]
    forwarded = [row for row in rows if row.get("gate_forward")]
    candidate_types = Counter((row.get("candidate_parsed_response") or {}).get("candidate_type") for row in rows)
    promptnode_families = Counter((row.get("candidate_parsed_response") or {}).get("promptnode_family") for row in rows)
    all_forwarded = len(forwarded) == len(rows) and bool(rows)
    return {
        "run_id": "R381",
        "title": "OptionBinding fresh eval analysis",
        "claim_boundary": (
            "R381 analyzes R380. The fresh result is positive no-harm on 24 new history items, but because the "
            "candidate path forwards every item, a plain-requery control is required before attributing the gain to "
            "PromptNode/PromptEdge graph structure."
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
        "option_binding_edge_applied_count": sum(1 for row in rows if row.get("option_binding_edge_applied")),
        "gate_forward_count": len(forwarded),
        "fixes": len(fixes),
        "harms": len(harms),
        "wrong_forward_count": len(wrong_forward),
        "fix_task_ids": [row.get("task_id") for row in fixes],
        "harm_task_ids": [row.get("task_id") for row in harms],
        "wrong_forward_task_ids": [row.get("task_id") for row in wrong_forward],
        "candidate_type_counts": dict(sorted(candidate_types.items())),
        "promptnode_family_counts": dict(sorted(promptnode_families.items())),
        "api_cost": r380.get("api_cost"),
        "prompt_tokens": r380.get("prompt_tokens"),
        "completion_tokens": r380.get("completion_tokens"),
        "claim_permissions": {
            "fresh_positive_delta_no_harm_claim_allowed": hybrid_correct > arg_correct and not harms,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "claim_risks": {
            "plain_requery_control_required": all_forwarded,
            "second_call_prompt_strength_confound": all_forwarded,
            "single_subject_history_only": True,
            "sample_size_still_small": len(rows) < 100,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R382_plain_requery_control_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R381 OptionBinding Fresh Eval Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- ARG: `{summary['arg_correct']}/{summary['records']}`",
        f"- Hybrid: `{summary['hybrid_correct']}/{summary['records']}`",
        f"- Delta correct: `{summary['delta_correct']}`",
        f"- Candidate labels / edge-applied: `{summary['candidate_label_count']}/{summary['option_binding_edge_applied_count']}`",
        f"- Gate forward/fix/harm/wrong-forward: `{summary['gate_forward_count']}/{summary['fixes']}/{summary['harms']}/{summary['wrong_forward_count']}`",
        f"- Fix tasks: `{summary['fix_task_ids']}`",
        f"- Plain requery control required: `{summary['claim_risks']['plain_requery_control_required']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run(
    r380_results: str = DEFAULT_R380_RESULTS,
    r380_summary: str = DEFAULT_R380_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_option_binding_fresh_analysis(r380_results=r380_results, r380_summary=r380_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R380 OptionBinding fresh eval.")
    parser.add_argument("--r380_results", default=DEFAULT_R380_RESULTS)
    parser.add_argument("--r380_summary", default=DEFAULT_R380_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
