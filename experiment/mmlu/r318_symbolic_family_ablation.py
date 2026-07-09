from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r301_conservative_census_gate import normalize_label
from experiment.mmlu.r303_audit_exclusion_protocol import EXCLUDED_TASK_IDS
from experiment.mmlu.r305_nonmath_promptnode_library import propose_nonmath_candidate
from experiment.mmlu.r306_nonmath_stack_eval import should_forward_nonmath


DEFAULT_ARG_JSONL = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl"
DEFAULT_R306_SUMMARY = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r318_symbolic_family_ablation_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r318_symbolic_family_ablation_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r318_symbolic_family_ablation_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with _repo_path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def apply_nonmath_only(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    task_id = str(out.get("task_id") or "")
    audit_excluded = task_id in EXCLUDED_TASK_IDS or bool(out.get("audit_excluded"))
    arg_prediction = normalize_label(out.get("predicted_answer") or out.get("arg_prediction"))
    true_answer = normalize_label(out.get("true_answer"))
    candidate = propose_nonmath_candidate(out)
    forward = (not audit_excluded) and should_forward_nonmath(candidate, arg_prediction)
    predicted = normalize_label(candidate.get("candidate_label")) if forward else arg_prediction
    arg_correct = arg_prediction == true_answer if true_answer else None
    is_correct = predicted == true_answer if true_answer else None
    out.update(
        {
            "run_id": "R318",
            "audit_excluded": audit_excluded,
            "removed_component": "symbolic_verifier_family",
            "arg_prediction": arg_prediction,
            "predicted_answer": predicted,
            "candidate": candidate,
            "nonmath_forward": forward,
            "is_correct": is_correct,
            "arg_is_correct": arg_correct,
            "fix": arg_correct is False and is_correct is True,
            "harm": arg_correct is True and is_correct is False,
            "decision_rule": f"forward_{candidate.get('candidate_type')}" if forward else "keep_arg_nonmath_only",
            "claim_boundary": "R318 removes symbolic verifier family and replays only non-math PromptNodes over ARG baseline.",
        }
    )
    return out


def summarize(rows: List[Dict[str, Any]], r306: Dict[str, Any]) -> Dict[str, Any]:
    main = [row for row in rows if not row.get("audit_excluded")]
    arg_correct = sum(1 for row in main if row.get("arg_is_correct"))
    nonmath_correct = sum(1 for row in main if row.get("is_correct"))
    fixes = sum(1 for row in main if row.get("fix"))
    harms = sum(1 for row in main if row.get("harm"))
    full_correct = int(r306.get("main_correct", 0))
    total = len(main)
    return {
        "run_id": "R318",
        "title": "Symbolic verifier family ablation",
        "claim_boundary": "Offline ablation only. It removes the symbolic/math verifier family and keeps only non-math PromptNodes over ARG baseline.",
        "no_api": True,
        "broad_api": False,
        "removed_component": "symbolic_verifier_family",
        "main_records": total,
        "arg_main": f"{arg_correct}/{total}",
        "nonmath_only_main": f"{nonmath_correct}/{total}",
        "full_r306_main": f"{full_correct}/{total}",
        "nonmath_only_fix_harm": f"{fixes}/{harms}",
        "nonmath_only_switches": sum(1 for row in main if row.get("nonmath_forward")),
        "symbolic_family_delta": full_correct - nonmath_correct,
        "nonmath_only_delta_vs_arg": nonmath_correct - arg_correct,
        "training_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R319_ablation_table_update",
    }


def build_symbolic_ablation_summary(
    arg_jsonl: str = DEFAULT_ARG_JSONL,
    r306_summary: str = DEFAULT_R306_SUMMARY,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = [apply_nonmath_only(row) for row in load_jsonl(arg_jsonl)]
    return rows, summarize(rows, _load_json(r306_summary))


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R318 Symbolic Verifier Family Ablation",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- ARG baseline: `{summary['arg_main']}`",
            f"- Non-math only: `{summary['nonmath_only_main']}`",
            f"- Full R306: `{summary['full_r306_main']}`",
            f"- Non-math fix/harm: `{summary['nonmath_only_fix_harm']}`",
            f"- Symbolic family delta: `{summary['symbolic_family_delta']}`",
            "",
        ]
    )


def run(
    arg_jsonl: str = DEFAULT_ARG_JSONL,
    r306_summary: str = DEFAULT_R306_SUMMARY,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    rows, summary = build_symbolic_ablation_summary(arg_jsonl=arg_jsonl, r306_summary=r306_summary)
    summary.update(
        {
            "arg_jsonl": arg_jsonl,
            "r306_summary": r306_summary,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    write_jsonl(output_jsonl, rows)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R318 symbolic verifier family ablation.")
    parser.add_argument("--arg_jsonl", default=DEFAULT_ARG_JSONL)
    parser.add_argument("--r306_summary", default=DEFAULT_R306_SUMMARY)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
