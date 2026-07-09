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


DEFAULT_INPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r414_definition_challenge_gate_analysis_report.md"


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


def _subject_breakdown(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[str(row.get("subject"))].append(row)
    out: Dict[str, Dict[str, Any]] = {}
    for subject, values in sorted(buckets.items()):
        arg = sum(1 for row in values if row.get("arg_correct"))
        candidate = sum(1 for row in values if row.get("candidate_correct"))
        hybrid = sum(1 for row in values if row.get("final_correct"))
        out[subject] = {
            "records": len(values),
            "arg_correct": arg,
            "candidate_correct": candidate,
            "hybrid_correct": hybrid,
            "delta_correct": hybrid - arg,
            "gate_forward_count": sum(1 for row in values if row.get("gate_forward")),
            "fixes": sum(1 for row in values if row.get("fix")),
            "harms": sum(1 for row in values if row.get("harm")),
            "wrong_forward_count": sum(1 for row in values if row.get("wrong_forward")),
        }
    return out


def build_definition_challenge_analysis(input_jsonl: str = DEFAULT_INPUT_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(input_jsonl)
    arg_correct = sum(1 for row in rows if row.get("arg_correct"))
    hybrid_correct = sum(1 for row in rows if row.get("final_correct"))
    candidate_correct = sum(1 for row in rows if row.get("candidate_correct"))
    fixes = [row["task_id"] for row in rows if row.get("fix")]
    harms = [row["task_id"] for row in rows if row.get("harm")]
    wrong_forwards = [row["task_id"] for row in rows if row.get("wrong_forward")]
    candidate_oracle_fixes = [
        row["task_id"] for row in rows if not row.get("arg_correct") and row.get("candidate_correct")
    ]
    candidate_oracle_harms = [
        row["task_id"] for row in rows if row.get("arg_correct") and not row.get("candidate_correct")
    ]
    pruned_candidate_harms = [
        row["task_id"]
        for row in rows
        if row.get("arg_correct") and not row.get("candidate_correct") and not row.get("gate_forward")
    ]
    gate_block_reason_counts = Counter(reason for row in rows for reason in row.get("gate_block_reasons", []))
    narrow_allowed = hybrid_correct > arg_correct and not harms and not wrong_forwards
    return {
        "run_id": "R414",
        "title": "DefinitionChallenge gate analysis",
        "claim_boundary": (
            "R414 analyzes a fresh targeted nonmath split. It supports only a narrow DefinitionChallenge "
            "positive/no-harm claim; it does not support broad nonmath generalization."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "arg_correct": arg_correct,
        "hybrid_correct": hybrid_correct,
        "candidate_correct": candidate_correct,
        "delta_correct": hybrid_correct - arg_correct,
        "candidate_pool_delta": candidate_correct - arg_correct,
        "arg_accuracy": round(arg_correct / len(rows), 6) if rows else None,
        "hybrid_accuracy": round(hybrid_correct / len(rows), 6) if rows else None,
        "candidate_accuracy": round(candidate_correct / len(rows), 6) if rows else None,
        "gate_forward_count": sum(1 for row in rows if row.get("gate_forward")),
        "fixes": len(fixes),
        "harms": len(harms),
        "wrong_forward_count": len(wrong_forwards),
        "fix_task_ids": fixes,
        "harm_task_ids": harms,
        "wrong_forward_task_ids": wrong_forwards,
        "candidate_oracle_fix_task_ids": candidate_oracle_fixes,
        "candidate_oracle_harm_task_ids": candidate_oracle_harms,
        "selection_contribution": {
            "gate_improves_over_arg": hybrid_correct > arg_correct,
            "gate_improves_over_candidate_pool": hybrid_correct > candidate_correct,
            "candidate_pool_alone_not_better_than_arg": candidate_correct <= arg_correct,
            "pruned_candidate_harms": len(pruned_candidate_harms),
            "pruned_candidate_harm_task_ids": pruned_candidate_harms,
        },
        "subject_breakdown": _subject_breakdown(rows),
        "gate_block_reason_counts": dict(gate_block_reason_counts),
        "claim_permissions": {
            "narrow_definition_challenge_claim_allowed": narrow_allowed,
            "broad_nonmath_claim_allowed": False,
            "main_paper_claim_allowed": False,
            "needs_external_integrity_audit": True,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R415_update_claim_matrix_after_nonmath_positive",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R414 DefinitionChallenge Gate Analysis",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- ARG / hybrid / candidate correct: `{summary['arg_correct']}/{summary['hybrid_correct']}/{summary['candidate_correct']}`",
        f"- Delta: `{summary['delta_correct']}`",
        f"- Fix/harm/wrong-forward: `{summary['fixes']}/{summary['harms']}/{summary['wrong_forward_count']}`",
        f"- Gate improves over candidate pool: `{summary['selection_contribution']['gate_improves_over_candidate_pool']}`",
        "",
        "## Subject Breakdown",
        "",
    ]
    rows.extend(
        f"- `{subject}`: ARG `{row['arg_correct']}/{row['records']}`, hybrid `{row['hybrid_correct']}/{row['records']}`, delta `{row['delta_correct']}`"
        for subject, row in summary["subject_breakdown"].items()
    )
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    input_jsonl: str = DEFAULT_INPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_definition_challenge_analysis(input_jsonl=input_jsonl)
    summary.update({"input_jsonl": input_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R413 DefinitionChallenge gate run.")
    parser.add_argument("--input_jsonl", default=DEFAULT_INPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
