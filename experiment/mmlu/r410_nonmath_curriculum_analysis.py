from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r409_nonmath_curriculum_api_execution import conservative_curriculum_gate


DEFAULT_INPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r409_nonmath_curriculum_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r410_nonmath_curriculum_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r410_nonmath_curriculum_analysis_report.md"


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


def _repair_embedded_json_fields(parsed: Dict[str, Any]) -> Dict[str, Any]:
    text = str(parsed.get("rationale") or "")
    repaired = dict(parsed)
    for key in ["node_agreement_count", "node_disagreement_count", "contradiction_count"]:
        match = re.search(rf'"{key}"\s*:\s*([0-9]+)', text)
        if match:
            repaired[key] = int(match.group(1))
    for key in ["confidence", "definition_anchor_confidence", "nearest_distractor_margin", "memory_bridge_write_confidence"]:
        match = re.search(rf'"{key}"\s*:\s*([0-9.]+)', text)
        if match:
            repaired[key] = float(match.group(1))
    for key in ["ambiguity_flag", "adversarial_challenge_pass", "option_binding_contract_pass"]:
        match = re.search(rf'"{key}"\s*:\s*(true|false)', text, flags=re.I)
        if match:
            repaired[key] = match.group(1).lower() == "true"
    match = re.search(r'"nearest_distractor"\s*:\s*"([A-E])"', text)
    if match:
        repaired["nearest_distractor"] = match.group(1)
    return repaired


def _score_replay(rows: List[Dict[str, Any]], repair_parser: bool) -> Dict[str, Any]:
    forward_task_ids: List[str] = []
    fix_task_ids: List[str] = []
    harm_task_ids: List[str] = []
    wrong_forward_task_ids: List[str] = []
    correct = 0
    for row in rows:
        parsed = row.get("candidate_parsed_response") or {}
        if repair_parser:
            parsed = _repair_embedded_json_fields(parsed)
        gate = conservative_curriculum_gate(parsed)
        candidate = str(parsed.get("candidate_label") or row.get("candidate_label") or "").strip().upper()[:1]
        forward = bool(gate.get("forward") and candidate)
        final = candidate if forward else row.get("arg_prediction")
        is_correct = final == row.get("true_answer")
        correct += int(is_correct)
        if forward:
            forward_task_ids.append(row["task_id"])
        if row.get("arg_prediction") != row.get("true_answer") and is_correct:
            fix_task_ids.append(row["task_id"])
        if row.get("arg_prediction") == row.get("true_answer") and not is_correct:
            harm_task_ids.append(row["task_id"])
        if forward and final != row.get("true_answer"):
            wrong_forward_task_ids.append(row["task_id"])
    return {
        "hybrid_correct": correct,
        "gate_forward_count": len(forward_task_ids),
        "fixes": len(fix_task_ids),
        "harms": len(harm_task_ids),
        "wrong_forward_count": len(wrong_forward_task_ids),
        "forward_task_ids": forward_task_ids,
        "fix_task_ids": fix_task_ids,
        "harm_task_ids": harm_task_ids,
        "wrong_forward_task_ids": wrong_forward_task_ids,
    }


def build_curriculum_analysis(input_jsonl: str = DEFAULT_INPUT_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(input_jsonl)
    arg_correct = sum(1 for row in rows if row.get("arg_correct"))
    hybrid_correct = sum(1 for row in rows if row.get("final_correct"))
    candidate_correct = sum(1 for row in rows if row.get("candidate_correct"))
    candidate_oracle_fix_ids = [
        row["task_id"] for row in rows if not row.get("arg_correct") and row.get("candidate_correct")
    ]
    candidate_oracle_harm_ids = [
        row["task_id"] for row in rows if row.get("arg_correct") and not row.get("candidate_correct")
    ]
    label_but_zero_fields = [
        row["task_id"]
        for row in rows
        if row.get("candidate_label")
        and (row.get("candidate_parsed_response") or {}).get("node_agreement_count", 0) == 0
    ]
    rationale_starts_json = [
        row["task_id"]
        for row in rows
        if str((row.get("candidate_parsed_response") or {}).get("rationale") or "").lstrip().startswith("{")
    ]
    by_subject: Dict[str, List[int]] = defaultdict(lambda: [0, 0, 0, 0])
    for row in rows:
        bucket = by_subject[str(row.get("subject"))]
        bucket[0] += 1
        bucket[1] += int(bool(row.get("arg_correct")))
        bucket[2] += int(bool(row.get("candidate_correct")))
        bucket[3] += int(bool(row.get("final_correct")))
    original_replay = _score_replay(rows, repair_parser=False)
    repaired_replay = _score_replay(rows, repair_parser=True)
    return {
        "run_id": "R410",
        "title": "Nonmath curriculum analysis",
        "claim_boundary": (
            "R410 analyzes R409. It shows candidate-level signal but no deployed positive gain. "
            "It cannot support a positive nonmath claim."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "arg_correct": arg_correct,
        "hybrid_correct": hybrid_correct,
        "candidate_correct": candidate_correct,
        "delta_correct": hybrid_correct - arg_correct,
        "candidate_oracle_delta": candidate_correct - arg_correct,
        "candidate_oracle_fixes": len(candidate_oracle_fix_ids),
        "candidate_oracle_harms": len(candidate_oracle_harm_ids),
        "candidate_oracle_fix_task_ids": candidate_oracle_fix_ids,
        "candidate_oracle_harm_task_ids": candidate_oracle_harm_ids,
        "original_gate_replay": original_replay,
        "parser_repair": {
            "label_but_zero_node_fields": len(label_but_zero_fields),
            "rationale_starts_json": len(rationale_starts_json),
            "affected_task_ids": sorted(set(label_but_zero_fields + rationale_starts_json)),
        },
        "parser_repair_replay": repaired_replay,
        "gate_block_reason_counts": dict(
            Counter(reason for row in rows for reason in row.get("gate_block_reasons", []))
        ),
        "subject_breakdown": {
            subject: {"records": values[0], "arg_correct": values[1], "candidate_correct": values[2], "hybrid_correct": values[3]}
            for subject, values in sorted(by_subject.items())
        },
        "claim_permissions": {
            "positive_nonmath_claim_allowed": False,
            "candidate_signal_claim_allowed": True,
            "parser_repair_required": bool(label_but_zero_fields),
            "learned_gate_ablation_allowed_next": True,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R411_curriculum_gate_ablation_and_goal_audit",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R410 Nonmath Curriculum Analysis",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['records']}`",
            f"- ARG / hybrid / candidate correct: `{summary['arg_correct']}/{summary['hybrid_correct']}/{summary['candidate_correct']}`",
            f"- Candidate oracle fixes/harms: `{summary['candidate_oracle_fixes']}/{summary['candidate_oracle_harms']}`",
            f"- Parser repair affected tasks: `{summary['parser_repair']['label_but_zero_node_fields']}`",
            f"- Parser-repair replay correct/fix/harm: `{summary['parser_repair_replay']['hybrid_correct']}/{summary['parser_repair_replay']['fixes']}/{summary['parser_repair_replay']['harms']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    input_jsonl: str = DEFAULT_INPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_curriculum_analysis(input_jsonl=input_jsonl)
    summary.update({"input_jsonl": input_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R409 nonmath curriculum run.")
    parser.add_argument("--input_jsonl", default=DEFAULT_INPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
