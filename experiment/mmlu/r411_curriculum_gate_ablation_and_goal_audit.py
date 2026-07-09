from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r409_nonmath_curriculum_api_execution import conservative_curriculum_gate
from experiment.mmlu.r410_nonmath_curriculum_analysis import _repair_embedded_json_fields


DEFAULT_INPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r409_nonmath_curriculum_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r411_curriculum_gate_ablation_and_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r411_curriculum_gate_ablation_and_goal_audit_report.md"


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


def _candidate(row: Dict[str, Any], repaired: Dict[str, Any]) -> str:
    return str(repaired.get("candidate_label") or row.get("candidate_label") or "").strip().upper()[:1]


def _relaxed_margin_015(row: Dict[str, Any], repaired: Dict[str, Any]) -> bool:
    return bool(
        _candidate(row, repaired)
        and float(repaired.get("confidence") or 0) >= 0.85
        and int(repaired.get("node_agreement_count") or 0) >= 3
        and int(repaired.get("node_disagreement_count") or 0) <= 1
        and int(repaired.get("contradiction_count") or 0) == 0
        and not bool(repaired.get("ambiguity_flag"))
        and bool(repaired.get("adversarial_challenge_pass"))
        and float(repaired.get("nearest_distractor_margin") or 0) >= 0.15
        and bool(repaired.get("option_binding_contract_pass"))
        and float(repaired.get("memory_bridge_write_confidence") or 0) >= 0.6
    )


def _parser_repair_conservative(row: Dict[str, Any], repaired: Dict[str, Any]) -> bool:
    return bool(conservative_curriculum_gate(repaired).get("forward") and _candidate(row, repaired))


def _logical_fallacy_definition_gate(row: Dict[str, Any], repaired: Dict[str, Any]) -> bool:
    return row.get("subject") == "logical_fallacies" and _relaxed_margin_015(row, repaired)


def _non_sociology_relaxed_gate(row: Dict[str, Any], repaired: Dict[str, Any]) -> bool:
    return row.get("subject") != "sociology" and _relaxed_margin_015(row, repaired)


def _logic_moral_philosophy_gate(row: Dict[str, Any], repaired: Dict[str, Any]) -> bool:
    return row.get("subject") in {"logical_fallacies", "moral_disputes", "philosophy"} and _relaxed_margin_015(row, repaired)


def _score_gate(rows: List[Dict[str, Any]], name: str, gate_fn: Callable[[Dict[str, Any], Dict[str, Any]], bool]) -> Dict[str, Any]:
    forward_ids: List[str] = []
    fix_ids: List[str] = []
    harm_ids: List[str] = []
    wrong_forward_ids: List[str] = []
    correct = 0
    for row in rows:
        repaired = _repair_embedded_json_fields(row.get("candidate_parsed_response") or {})
        candidate = _candidate(row, repaired)
        forward = bool(gate_fn(row, repaired) and candidate)
        final = candidate if forward else row.get("arg_prediction")
        is_correct = final == row.get("true_answer")
        correct += int(is_correct)
        if forward:
            forward_ids.append(row["task_id"])
        if row.get("arg_prediction") != row.get("true_answer") and is_correct:
            fix_ids.append(row["task_id"])
        if row.get("arg_prediction") == row.get("true_answer") and not is_correct:
            harm_ids.append(row["task_id"])
        if forward and final != row.get("true_answer"):
            wrong_forward_ids.append(row["task_id"])
    arg_correct = sum(1 for row in rows if row.get("arg_correct"))
    return {
        "name": name,
        "hybrid_correct": correct,
        "delta_correct": correct - arg_correct,
        "gate_forward_count": len(forward_ids),
        "fixes": len(fix_ids),
        "harms": len(harm_ids),
        "wrong_forward_count": len(wrong_forward_ids),
        "forward_task_ids": forward_ids,
        "fix_task_ids": fix_ids,
        "harm_task_ids": harm_ids,
        "wrong_forward_task_ids": wrong_forward_ids,
    }


def build_gate_ablation(input_jsonl: str = DEFAULT_INPUT_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(input_jsonl)
    gate_ablations = [
        _score_gate(rows, "parser_repair_conservative", _parser_repair_conservative),
        _score_gate(rows, "relaxed_margin_015", _relaxed_margin_015),
        _score_gate(rows, "logical_fallacy_definition_gate", _logical_fallacy_definition_gate),
        _score_gate(rows, "non_sociology_relaxed_gate", _non_sociology_relaxed_gate),
        _score_gate(rows, "logic_moral_philosophy_gate", _logic_moral_philosophy_gate),
    ]
    no_harm = [row for row in gate_ablations if row["harms"] == 0]
    best = sorted(no_harm, key=lambda row: (-row["hybrid_correct"], row["wrong_forward_count"], row["gate_forward_count"], row["name"]))[0]
    return {
        "run_id": "R411",
        "title": "Curriculum gate ablation and goal audit",
        "claim_boundary": (
            "R411 is a same-split diagnostic ablation. It may define a prospective gate hypothesis, "
            "but it cannot support a positive nonmath paper claim."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "arg_correct": sum(1 for row in rows if row.get("arg_correct")),
        "candidate_correct": sum(1 for row in rows if row.get("candidate_correct")),
        "gate_ablations": gate_ablations,
        "best_diagnostic_gate": best,
        "same_split_diagnostic_only": True,
        "prospective_gate_hypothesis": {
            "name": "definition_challenge_gate",
            "source": "logical_fallacy_definition_gate",
            "description": (
                "Forward only for definition-heavy logical-fallacy style items when parser-repaired node evidence "
                "passes relaxed margin 0.15, contradiction-free, adversarial-challenge, and option-binding contracts."
            ),
            "must_be_tested_on_fresh_split": True,
        },
        "iterations_since_last_goal_check": ["R407", "R408", "R409", "R410", "R411"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_designer_remains_main_baseline": True,
            "promptnode_first_class_boundary_preserved": True,
            "nonmath_positive_claim_not_yet_supported": True,
            "fresh_transfer_required_next": True,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "positive_nonmath_claim_allowed": False,
            "same_split_gate_ablation_claim_allowed": False,
            "fresh_prospective_gate_preflight_allowed_next": True,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R412_fresh_definition_challenge_gate_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R411 Curriculum Gate Ablation And Goal Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Best diagnostic gate: `{summary['best_diagnostic_gate']['name']}`",
        f"- Best correct/fix/harm/wrong-forward: `{summary['best_diagnostic_gate']['hybrid_correct']}/{summary['best_diagnostic_gate']['fixes']}/{summary['best_diagnostic_gate']['harms']}/{summary['best_diagnostic_gate']['wrong_forward_count']}`",
        f"- Same split only: `{summary['same_split_diagnostic_only']}`",
        "",
        "## Gate Ablations",
        "",
    ]
    rows.extend(
        f"- `{row['name']}`: correct `{row['hybrid_correct']}`, fix/harm/wrong `{row['fixes']}/{row['harms']}/{row['wrong_forward_count']}`"
        for row in summary["gate_ablations"]
    )
    rows.extend(["", "## Goal Check", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    input_jsonl: str = DEFAULT_INPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_gate_ablation(input_jsonl=input_jsonl)
    summary.update({"input_jsonl": input_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R411 curriculum gate ablation and goal audit.")
    parser.add_argument("--input_jsonl", default=DEFAULT_INPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
