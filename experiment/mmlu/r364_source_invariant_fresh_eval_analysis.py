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


DEFAULT_R363_RESULTS = "experiment/mmlu/run_logs/mmlu_r363_source_invariant_fresh_eval_api_results.jsonl"
DEFAULT_R363_SUMMARY = "experiment/mmlu/res_logs/mmlu_r363_source_invariant_fresh_eval_api_execution_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r364_source_invariant_fresh_eval_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r364_source_invariant_fresh_eval_analysis_report.md"


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


def build_fresh_eval_analysis(
    r363_results: str = DEFAULT_R363_RESULTS,
    r363_summary: str = DEFAULT_R363_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r363_results)
    r363 = _load_json(r363_summary)
    arg_correct = sum(1 for row in rows if row.get("arg_correct"))
    hybrid_correct = sum(1 for row in rows if row.get("final_correct"))
    forwarded = [row for row in rows if row.get("gate_forward")]
    wrong_forward = [row for row in forwarded if not row.get("final_correct")]
    missed_fixes = [row for row in rows if not row.get("arg_correct") and not row.get("final_correct") and not row.get("gate_forward")]
    fixes = [row for row in rows if row.get("fix")]
    harms = [row for row in rows if row.get("harm")]
    return {
        "run_id": "R364",
        "title": "Source-invariant fresh eval analysis",
        "claim_boundary": (
            "R364 analyzes the executed R363 fresh eval. It supports a small positive no-harm delta, but not an "
            "SCI-Q2-ready main claim because the gain is only one item and one wrong forward remains."
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
        "fix_task_ids": [row.get("task_id") for row in fixes],
        "wrong_forward_task_ids": [row.get("task_id") for row in wrong_forward],
        "missed_fix_task_ids": [row.get("task_id") for row in missed_fixes],
        "api_cost": r363.get("api_cost"),
        "prompt_tokens": r363.get("prompt_tokens"),
        "completion_tokens": r363.get("completion_tokens"),
        "claim_permissions": {
            "fresh_positive_delta_no_harm_claim_allowed": hybrid_correct > arg_correct and not harms,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R365_wrong_forward_and_missed_fix_analysis",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R364 Source-Invariant Fresh Eval Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- ARG: `{summary['arg_correct']}/{summary['records']}`",
        f"- Hybrid: `{summary['hybrid_correct']}/{summary['records']}`",
        f"- Delta correct: `{summary['delta_correct']}`",
        f"- Gate forward/fix/harm/wrong-forward: `{summary['gate_forward_count']}/{summary['fixes']}/{summary['harms']}/{summary['wrong_forward_count']}`",
        f"- Fix tasks: `{summary['fix_task_ids']}`",
        f"- Wrong-forward tasks: `{summary['wrong_forward_task_ids']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run(
    r363_results: str = DEFAULT_R363_RESULTS,
    r363_summary: str = DEFAULT_R363_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_fresh_eval_analysis(r363_results=r363_results, r363_summary=r363_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R363 source-invariant fresh eval.")
    parser.add_argument("--r363_results", default=DEFAULT_R363_RESULTS)
    parser.add_argument("--r363_summary", default=DEFAULT_R363_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
