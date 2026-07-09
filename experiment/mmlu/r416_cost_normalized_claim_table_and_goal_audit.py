from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R271_AQUA = "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json"
DEFAULT_R306_MMLU = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_R316_CONTROL = "experiment/mmlu/res_logs/mmlu_r316_promptedge_cost_controls_summary.json"
DEFAULT_R413_COST = "experiment/mmlu/res_logs/mmlu_r413_definition_challenge_gate_api_execution_summary.json"
DEFAULT_R414_ANALYSIS = "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r416_cost_normalized_claim_table_and_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r416_cost_normalized_claim_table_and_goal_audit_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _parse_score(score: str) -> Tuple[Optional[int], Optional[int]]:
    try:
        correct, total = str(score).split("/", 1)
        return int(correct), int(total)
    except (ValueError, TypeError):
        return None, None


def _cost_row(
    row_id: str,
    slice_name: str,
    score: str,
    cost: Optional[float],
    source: str,
    role: str,
    fix_harm_wrong: str = "n/a",
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    note: str = "",
) -> Dict[str, Any]:
    correct, total = _parse_score(score)
    accuracy = round(correct / total, 6) if correct is not None and total else None
    cost_per_task = round(cost / total, 6) if cost is not None and total else None
    correct_per_cost = round(correct / cost, 6) if cost and correct is not None else None
    accuracy_per_cost = round(accuracy / cost, 6) if cost and accuracy is not None else None
    return {
        "id": row_id,
        "slice": slice_name,
        "score": score,
        "accuracy": accuracy,
        "cost": cost,
        "cost_per_task": cost_per_task,
        "correct_per_cost": correct_per_cost,
        "accuracy_per_cost": accuracy_per_cost,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "fix_harm_wrong": fix_harm_wrong,
        "source": source,
        "role": role,
        "note": note,
    }


def build_cost_table(
    r271_aqua: str = DEFAULT_R271_AQUA,
    r306_mmlu: str = DEFAULT_R306_MMLU,
    r316_control: str = DEFAULT_R316_CONTROL,
    r413_cost: str = DEFAULT_R413_COST,
    r414_analysis: str = DEFAULT_R414_ANALYSIS,
) -> Dict[str, Any]:
    aqua = _load_json(r271_aqua)
    r306 = _load_json(r306_mmlu)
    r316 = _load_json(r316_control)
    r413 = _load_json(r413_cost)
    r414 = _load_json(r414_analysis)
    variants = aqua.get("variants", {})
    control_cost_per_api_variant = round(float(r316.get("api_cost", 0.0)) / 2.0, 6) if r316 else None
    cost_rows: List[Dict[str, Any]] = []
    if variants:
        cost_rows.extend(
            [
                _cost_row(
                    "AQuA_ARG_baseline",
                    "AQuA_tail34_official",
                    variants["ARG"]["official"],
                    variants["ARG"]["cost"],
                    r271_aqua,
                    "ARG baseline",
                    note="AQuA replay cost from R271.",
                ),
                _cost_row(
                    "AQuA_R068_cost_reduced",
                    "AQuA_tail34_official",
                    variants["R068"]["official"],
                    variants["R068"]["cost"],
                    r271_aqua,
                    "cost-reduced PromptNode replay",
                    note="Retains R065 official score with lower multi-view cost.",
                ),
                _cost_row(
                    "AQuA_R267_safety_cost",
                    "AQuA_tail34_audit_boundary",
                    variants["R267"]["correct_task114"],
                    variants["R267"]["cost"],
                    r271_aqua,
                    "cost-reduced plus safety-gated replay",
                    note="Audit-boundary interpretation; not the highest official score.",
                ),
            ]
        )
    if r306:
        cost_rows.append(
            _cost_row(
                "MMLU_STEM_R306_cost_missing",
                "MMLU_STEM_main97",
                f"{r306.get('main_correct')}/{r306.get('main_records')}",
                None,
                r306_mmlu,
                "MMLU STEM positive result with missing raw API cost",
                fix_harm_wrong=f"{r306.get('main_fixes')}/{r306.get('main_harms')}/n/a",
                note="Accuracy evidence exists, but the current summary lacks token/cost fields.",
            )
        )
    if r413 and r414:
        cost_rows.append(
            _cost_row(
                "MMLU_DefinitionChallenge_R413",
                "MMLU_definition_challenge_fresh24",
                f"{r413.get('hybrid_correct')}/{r413.get('tasks')}",
                float(r413.get("api_cost")),
                r413_cost,
                "fresh targeted nonmath PromptNode/PromptEdge gate",
                fix_harm_wrong=f"{r414.get('fixes')}/{r414.get('harms')}/{r414.get('wrong_forward_count')}",
                prompt_tokens=int(r413.get("prompt_tokens")),
                completion_tokens=int(r413.get("completion_tokens")),
                note="Cost includes both ARG direct baseline and DefinitionChallenge candidate calls.",
            )
        )
    if r316:
        plain = r316.get("by_variant", {}).get("plain_requery", {})
        cost_rows.append(
            _cost_row(
                "MMLU_plain_requery_R316",
                "MMLU_nonSTEM40_plain_requery_control",
                f"{plain.get('correct')}/{plain.get('records')}",
                control_cost_per_api_variant,
                r316_control,
                "cost-matched plain requery control",
                fix_harm_wrong=f"{plain.get('fixes')}/{plain.get('harms')}/n/a",
                prompt_tokens=None,
                completion_tokens=None,
                note="Approximate half of R316 total API cost, because node-only and plain-requery each made 40 API calls.",
            )
        )
    missing_cost_evidence = []
    if any(row["id"] == "MMLU_STEM_R306_cost_missing" and row["cost"] is None for row in cost_rows):
        missing_cost_evidence.append("MMLU_STEM_cost_missing")
    missing_cost_evidence.append("independent_integrity_audit_missing")
    return {
        "run_id": "R416",
        "title": "Cost-normalized claim table and goal audit",
        "claim_boundary": (
            "R416 prepares paper-facing cost rows from available evidence. It exposes missing cost fields instead of "
            "authorizing submission claims."
        ),
        "no_api": True,
        "broad_api": False,
        "cost_rows": cost_rows,
        "missing_cost_evidence": missing_cost_evidence,
        "cost_table_complete_for_submission": False,
        "iterations_since_last_goal_check": ["R412", "R413", "R414", "R415", "R416"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_designer_remains_main_baseline": True,
            "promptnode_first_class_boundary_preserved": True,
            "cost_reporting_gap_visible": True,
            "broad_nonmath_overclaim_blocked": True,
            "next_needs_case_study_and_audit": True,
        },
        "claim_permissions": {
            "cost_normalized_table_allowed": True,
            "cost_normalized_submission_claim_allowed": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R417_case_study_evidence_pack",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R416 Cost-Normalized Claim Table And Goal Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Row | Slice | Score | Cost | Cost/task | Correct/cost | Fix/Harm/Wrong | Role |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary["cost_rows"]:
        rows.append(
            f"| `{row['id']}` | `{row['slice']}` | `{row['score']}` | `{row['cost']}` | `{row['cost_per_task']}` | `{row['correct_per_cost']}` | `{row['fix_harm_wrong']}` | {row['role']} |"
        )
    rows.extend(["", "## Missing Cost Evidence", ""])
    rows.extend(f"- `{item}`" for item in summary["missing_cost_evidence"])
    rows.extend(["", "## Goal Check", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r271_aqua: str = DEFAULT_R271_AQUA,
    r306_mmlu: str = DEFAULT_R306_MMLU,
    r316_control: str = DEFAULT_R316_CONTROL,
    r413_cost: str = DEFAULT_R413_COST,
    r414_analysis: str = DEFAULT_R414_ANALYSIS,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_cost_table(
        r271_aqua=r271_aqua,
        r306_mmlu=r306_mmlu,
        r316_control=r316_control,
        r413_cost=r413_cost,
        r414_analysis=r414_analysis,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R416 cost-normalized claim table.")
    parser.add_argument("--r271_aqua", default=DEFAULT_R271_AQUA)
    parser.add_argument("--r306_mmlu", default=DEFAULT_R306_MMLU)
    parser.add_argument("--r316_control", default=DEFAULT_R316_CONTROL)
    parser.add_argument("--r413_cost", default=DEFAULT_R413_COST)
    parser.add_argument("--r414_analysis", default=DEFAULT_R414_ANALYSIS)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
