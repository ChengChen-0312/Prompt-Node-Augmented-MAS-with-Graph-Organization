from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r301_conservative_census_gate import VALID_LABELS, load_jsonl, normalize_label, write_json, write_jsonl, write_text
from experiment.mmlu.r303_audit_exclusion_protocol import EXCLUDED_TASK_IDS
from experiment.mmlu.r305_nonmath_promptnode_library import propose_nonmath_candidate


DEFAULT_R304_JSONL = "experiment/mmlu/run_logs/mmlu_r304_multi_trigger_safety_gate_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r306_nonmath_stack_eval_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r306_nonmath_stack_eval_report.md"


def _official(row: Dict[str, Any]) -> str:
    return normalize_label(row.get("true_answer"))


def _clean(row: Dict[str, Any]) -> str:
    return normalize_label(row.get("audit_clean_answer") or row.get("true_answer"))


def _current_prediction(row: Dict[str, Any]) -> str:
    return normalize_label(row.get("predicted_answer") or row.get("arg_prediction"))


def should_forward_nonmath(candidate: Dict[str, Any], current_prediction: str) -> bool:
    label = normalize_label(candidate.get("candidate_label"))
    if label not in VALID_LABELS or label == normalize_label(current_prediction):
        return False
    if float(candidate.get("confidence") or 0.0) < 0.95:
        return False
    if int(candidate.get("evidence_count") or 0) < 3:
        return False
    return str(candidate.get("candidate_type") or "") in {
        "option_semantic_consistency",
        "conceptual_all_of_these_consistency",
    }


def apply_nonmath_stack(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    task_id = str(out.get("task_id") or "")
    excluded = bool(out.get("audit_excluded")) or task_id in EXCLUDED_TASK_IDS
    current = _current_prediction(out)
    candidate = propose_nonmath_candidate(out)
    forward = (not excluded) and should_forward_nonmath(candidate, current)
    predicted = normalize_label(candidate.get("candidate_label")) if forward else current
    official = _official(out)
    clean = _clean(out)
    baseline_official = current == official if official in VALID_LABELS else None
    baseline_clean = current == clean if clean in VALID_LABELS else None
    official_correct = predicted == official if official in VALID_LABELS else None
    clean_correct = predicted == clean if clean in VALID_LABELS else None
    out.update(
        {
            "run_id": "R306",
            "audit_excluded": excluded,
            "r304_prediction": current,
            "predicted_answer": predicted,
            "candidate": candidate,
            "nonmath_forward": forward,
            "decision_rule": f"forward_{candidate['candidate_type']}" if forward else "keep_r304_nonmath_stack",
            "is_correct": official_correct,
            "audit_clean_is_correct": clean_correct,
            "r304_is_correct": baseline_official,
            "r304_audit_clean_is_correct": baseline_clean,
            "fix": baseline_official is False and official_correct is True,
            "harm": baseline_official is True and official_correct is False,
            "audit_clean_fix": baseline_clean is False and clean_correct is True,
            "audit_clean_harm": baseline_clean is True and clean_correct is False,
            "promptnode_roles": sorted(set((out.get("promptnode_roles") or []) + candidate.get("promptnode_roles", []))),
            "promptedge_permissions": ["read", "write", "forward"],
            "lifecycle_actions": candidate.get("lifecycle_actions", ["compress"]) if forward else ["compress", "prune"],
            "model_visible_features_only": True,
            "claim_boundary": "R306 stacks non-math PromptNodes on R304; audited tasks are excluded from main aggregation.",
        }
    )
    return out


def _count(rows: List[Dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if row.get(key))


def _slice_summary(rows: List[Dict[str, Any]], prefix: str) -> Dict[str, Any]:
    official = [row for row in rows if row.get("is_correct") is not None]
    clean = [row for row in rows if row.get("audit_clean_is_correct") is not None]
    fixes = _count(official, "fix")
    harms = _count(official, "harm")
    clean_fixes = _count(clean, "audit_clean_fix")
    clean_harms = _count(clean, "audit_clean_harm")
    return {
        f"{prefix}_records": len(rows),
        f"{prefix}_correct": _count(official, "is_correct"),
        f"{prefix}_accuracy": _count(official, "is_correct") / len(official) if official else None,
        f"{prefix}_audit_clean_correct": _count(clean, "audit_clean_is_correct"),
        f"{prefix}_audit_clean_accuracy": _count(clean, "audit_clean_is_correct") / len(clean) if clean else None,
        f"{prefix}_fixes": fixes,
        f"{prefix}_harms": harms,
        f"{prefix}_fix_harm": f"{fixes}/{harms}",
        f"{prefix}_audit_clean_fixes": clean_fixes,
        f"{prefix}_audit_clean_harms": clean_harms,
        f"{prefix}_audit_clean_fix_harm": f"{clean_fixes}/{clean_harms}",
        f"{prefix}_nonmath_switches": sum(1 for row in rows if row.get("nonmath_forward")),
    }


def summarize_nonmath_records(
    records: List[Dict[str, Any]],
    r304_main_correct: int,
    r304_main_audit_clean_correct: int,
) -> Dict[str, Any]:
    main = [row for row in records if not row.get("audit_excluded")]
    appendix = [row for row in records if row.get("audit_excluded")]
    summary = {
        "run_id": "R306",
        "title": "Non-math PromptNode stack evaluation",
        "claim_boundary": (
            "Offline stack over R304. Main aggregation excludes the three audited tasks; no training is started. "
            "R304 serves as the no-nonmath negative control."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "r304_main_correct": int(r304_main_correct),
        "r304_main_audit_clean_correct": int(r304_main_audit_clean_correct),
        "appendix_excluded_records": len(appendix),
        "excluded_task_ids": sorted(EXCLUDED_TASK_IDS),
        "switched_task_ids": [row.get("task_id") for row in records if row.get("nonmath_forward")],
        "negative_controls": {
            "no_nonmath_promptnodes": {
                "main_correct": int(r304_main_correct),
                "main_audit_clean_correct": int(r304_main_audit_clean_correct),
            }
        },
        "model_visible_features_only": all(row.get("model_visible_features_only") for row in records),
    }
    summary.update(_slice_summary(records, "full"))
    summary.update(_slice_summary(main, "main"))
    summary.update(_slice_summary(appendix, "appendix"))
    summary["main_delta_vs_r304"] = summary["main_correct"] - int(r304_main_correct)
    summary["main_audit_clean_delta_vs_r304"] = summary["main_audit_clean_correct"] - int(r304_main_audit_clean_correct)
    summary["beats_r304_main_official"] = summary["main_correct"] > int(r304_main_correct)
    summary["beats_r304_main_audit_clean"] = summary["main_audit_clean_correct"] > int(r304_main_audit_clean_correct)
    summary["no_harm_main_official"] = summary["main_harms"] == 0
    summary["no_harm_main_audit_clean"] = summary["main_audit_clean_harms"] == 0
    summary["training_authorized_next"] = False
    summary["transfer_superiority_claim_supported"] = (
        summary["beats_r304_main_official"]
        and summary["beats_r304_main_audit_clean"]
        and summary["no_harm_main_official"]
        and summary["no_harm_main_audit_clean"]
    )
    summary["sci_q2_ready"] = False
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R306 Non-Math PromptNode Stack Eval",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Main97: R306 `{summary['main_correct']}/{summary['main_records']}` vs R304 `{summary['r304_main_correct']}/{summary['main_records']}`; delta `{summary['main_delta_vs_r304']}`",
            f"- Main97 audit-clean: R306 `{summary['main_audit_clean_correct']}/{summary['main_records']}` vs R304 `{summary['r304_main_audit_clean_correct']}/{summary['main_records']}`; delta `{summary['main_audit_clean_delta_vs_r304']}`",
            f"- Main97 fix/harm: `{summary['main_fix_harm']}`; audit-clean `{summary['main_audit_clean_fix_harm']}`",
            f"- Nonmath switches: `{summary['main_nonmath_switches']}`; tasks `{summary['switched_task_ids']}`",
            f"- Negative control no-nonmath: `{summary['negative_controls']['no_nonmath_promptnodes']}`",
            "",
        ]
    )


def run(
    r304_jsonl: str = DEFAULT_R304_JSONL,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    source = load_jsonl(r304_jsonl)
    records = [apply_nonmath_stack(row) for row in source]
    main = [row for row in source if not row.get("audit_excluded")]
    r304_main_correct = sum(1 for row in main if row.get("is_correct"))
    r304_main_clean = sum(1 for row in main if row.get("audit_clean_is_correct"))
    summary = summarize_nonmath_records(records, r304_main_correct, r304_main_clean)
    summary.update(
        {
            "r304_jsonl": r304_jsonl,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    write_jsonl(output_jsonl, records)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R306 non-math PromptNode stack evaluation.")
    parser.add_argument("--r304_jsonl", default=DEFAULT_R304_JSONL)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
