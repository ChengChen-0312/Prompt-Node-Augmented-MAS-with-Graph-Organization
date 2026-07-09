from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R311_RESULTS = "experiment/mmlu/run_logs/mmlu_r311_nonstem_promptnode_results.jsonl"
DEFAULT_R310_SPLIT = "experiment/mmlu/run_logs/mmlu_r310_nonstem_transfer_preflight_records.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r312_nonstem_safety_replay_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r312_nonstem_safety_replay_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r312_nonstem_safety_replay_report.md"
VALID_LABELS = {"A", "B", "C", "D", "E"}


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


def normalize_label(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text[:1] if text[:1] in VALID_LABELS else ""


def _candidate_has_answer(candidate: Dict[str, Any]) -> bool:
    return normalize_label(candidate.get("candidate_label")) in VALID_LABELS


def apply_warning_only_safety_gate(row: Dict[str, Any], split_row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    if out.get("control_variant") != "proposed_nonstem_promptnode_promptedge":
        out["control_variant"] = "arg_baseline_fixed"
        out["safety_replay_reason"] = "arg_baseline_unchanged"
        return out

    candidate = dict(split_row.get("candidate") or {})
    true_answer = normalize_label(out.get("true_answer"))
    arg_prediction = normalize_label(out.get("arg_prediction"))
    original_prediction = normalize_label(out.get("predicted_answer"))
    warning_only = not _candidate_has_answer(candidate)

    if warning_only and original_prediction != arg_prediction:
        predicted = arg_prediction
        reason = "warning_only_candidate_no_answer_override"
    else:
        predicted = original_prediction or arg_prediction
        reason = "answer_candidate_or_no_switch_preserved"

    arg_is_correct = arg_prediction == true_answer if true_answer in VALID_LABELS else None
    is_correct = predicted == true_answer if true_answer in VALID_LABELS else None
    out.update(
        {
            "run_id": "R312",
            "control_variant": "proposed_nonstem_promptnode_promptedge_safety_replay",
            "predicted_answer": predicted,
            "is_correct": is_correct,
            "arg_is_correct": arg_is_correct,
            "fix": arg_is_correct is False and is_correct is True,
            "harm": arg_is_correct is True and is_correct is False,
            "candidate": candidate,
            "candidate_has_answer_label": not warning_only,
            "safety_replay_reason": reason,
            "claim_boundary": "R312 safety replay: warning-only PromptNodes may update/compress/prune but cannot override answers.",
        }
    )
    return out


def _variant_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    evaluated = [row for row in rows if row.get("is_correct") is not None]
    correct = sum(1 for row in evaluated if row.get("is_correct"))
    return {
        "records": len(rows),
        "evaluated_records": len(evaluated),
        "correct": correct,
        "accuracy": correct / len(evaluated) if evaluated else None,
        "fixes": sum(1 for row in evaluated if row.get("fix")),
        "harms": sum(1 for row in evaluated if row.get("harm")),
        "switches": sum(1 for row in evaluated if normalize_label(row.get("predicted_answer")) != normalize_label(row.get("arg_prediction"))),
    }


def build_safety_replay_records(r311_rows: List[Dict[str, Any]], split_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    split_lookup = {str(row.get("task_id") or ""): row for row in split_rows}
    outputs: List[Dict[str, Any]] = []
    for row in r311_rows:
        if row.get("control_variant") == "arg_baseline_fixed":
            out = dict(row)
            out["run_id"] = "R312"
            out["safety_replay_reason"] = "arg_baseline_unchanged"
            outputs.append(out)
        elif row.get("control_variant") == "proposed_nonstem_promptnode_promptedge":
            outputs.append(apply_warning_only_safety_gate(row, split_lookup.get(str(row.get("task_id") or ""), {})))
    return outputs


def summarize_replay(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_variant = {
        variant: _variant_summary([row for row in records if row.get("control_variant") == variant])
        for variant in sorted({str(row.get("control_variant")) for row in records})
    }
    arg = by_variant.get("arg_baseline_fixed", {})
    proposed = by_variant.get("proposed_nonstem_promptnode_promptedge_safety_replay", {})
    arg_correct = int(arg.get("correct", 0))
    proposed_correct = int(proposed.get("correct", 0))
    return {
        "run_id": "R312",
        "title": "Non-STEM warning-only safety replay and claim boundary",
        "claim_boundary": (
            "R312 is an offline safety replay over R311 raw outputs. It supports a non-STEM no-harm boundary "
            "only; it does not support a broad non-STEM improvement claim."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(records),
        "tasks": len({str(row.get("task_id")) for row in records}),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in records).items())),
        "by_variant": by_variant,
        "arg_main": f"{arg_correct}/{arg.get('evaluated_records', 0)}",
        "proposed_safety_replay_main": f"{proposed_correct}/{proposed.get('evaluated_records', 0)}",
        "delta_vs_arg": proposed_correct - arg_correct,
        "fix_harm_vs_arg": f"{proposed.get('fixes', 0)}/{proposed.get('harms', 0)}",
        "no_harm": int(proposed.get("harms", 0)) == 0,
        "beats_arg": proposed_correct > arg_correct,
        "claim_permissions": {
            "nonstem_no_harm_claim_allowed": int(proposed.get("harms", 0)) == 0,
            "nonstem_improvement_claim_allowed": proposed_correct > arg_correct,
            "broad_general_promptnode_claim_allowed": False,
            "training_authorized": False,
            "sci_q2_ready": False,
        },
        "interpretation": (
            "The current non-STEM PromptNodes are useful as warning/lifecycle nodes but not as answer-overriding nodes. "
            "Training should not learn to switch from warning-only candidates."
        ),
        "training_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R313_ablation_and_claim_matrix",
    }


def build_safety_replay_summary(
    r311_results: str = DEFAULT_R311_RESULTS,
    r310_split: str = DEFAULT_R310_SPLIT,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    records = build_safety_replay_records(load_jsonl(r311_results), load_jsonl(r310_split))
    return records, summarize_replay(records)


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R312 Non-STEM Safety Replay",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- ARG baseline: `{summary['arg_main']}`",
        f"- Safety replay: `{summary['proposed_safety_replay_main']}`",
        f"- Delta vs ARG: `{summary['delta_vs_arg']}`",
        f"- Fix/harm vs ARG: `{summary['fix_harm_vs_arg']}`",
        f"- No harm: `{summary['no_harm']}`",
        "",
        "## Interpretation",
        "",
        summary["interpretation"],
        "",
        "## Claim Permissions",
        "",
    ]
    rows.extend(f"- `{name}`: `{value}`" for name, value in summary["claim_permissions"].items())
    rows.append("")
    return "\n".join(rows)


def run(
    r311_results: str = DEFAULT_R311_RESULTS,
    r310_split: str = DEFAULT_R310_SPLIT,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    records, summary = build_safety_replay_summary(r311_results=r311_results, r310_split=r310_split)
    summary.update(
        {
            "r311_results": r311_results,
            "r310_split": r310_split,
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
    parser = argparse.ArgumentParser(description="Run R312 non-STEM warning-only safety replay.")
    parser.add_argument("--r311_results", default=DEFAULT_R311_RESULTS)
    parser.add_argument("--r310_split", default=DEFAULT_R310_SPLIT)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
