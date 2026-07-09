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


DEFAULT_R306_JSONL = "experiment/mmlu/run_logs/mmlu_r306_nonmath_stack_eval_results.jsonl"
DEFAULT_R309_SUMMARY = "experiment/mmlu/res_logs/mmlu_r309_negative_controls_summary.json"
DEFAULT_R327_PREDICTIONS_JSONL = "experiment/mmlu/run_logs/mmlu_r327_augmented_selector_retraining_dry_run_predictions.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r329_case_study_extraction_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r329_case_study_extraction_report.md"


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


def _verifier_repair_case(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    row = next(item for item in rows if item.get("nonmath_forward") and item.get("fix"))
    candidate = row.get("candidate") or {}
    return {
        "mechanism": "verifier_repair",
        "source_run": "R306",
        "task_id": row.get("task_id"),
        "subject": row.get("subject"),
        "baseline_answer": row.get("arg_prediction"),
        "promptnode_answer": row.get("predicted_answer"),
        "outcome": "fix",
        "promptnode_roles": candidate.get("promptnode_roles", []),
        "promptedge_permissions": candidate.get("promptedge_permissions", []),
        "lifecycle_actions": candidate.get("lifecycle_actions", []),
        "paper_use": "Main case study: semantic verifier forwards a concrete answer only when evidence count and confidence are high.",
    }


def _memory_bridge_case(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    row = next(item for item in rows if (item.get("candidate") or {}).get("candidate_type") == "memory_bridge_required")
    candidate = row.get("candidate") or {}
    return {
        "mechanism": "memory_bridge_prune",
        "source_run": "R306",
        "task_id": row.get("task_id"),
        "subject": row.get("subject"),
        "baseline_answer": row.get("arg_prediction"),
        "promptnode_answer": row.get("predicted_answer"),
        "outcome": "unresolved_signal_pruned",
        "promptnode_roles": candidate.get("promptnode_roles", []),
        "promptedge_permissions": candidate.get("promptedge_permissions", []),
        "lifecycle_actions": candidate.get("lifecycle_actions", []),
        "paper_use": "Boundary case: MemoryBridge identifies missing/truncated context, writes and compresses the signal, then prunes answer override.",
    }


def _promptedge_block_case(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    row = next(item for item in rows if item.get("source_run") == "R325" and not item.get("predicted_forward"))
    return {
        "mechanism": "promptedge_false_forward_block",
        "source_run": "R327",
        "source_variant": row.get("source_variant"),
        "source_ref_hash": row.get("source_ref_hash"),
        "outcome": "hard_negative_blocked",
        "promptnode_family": row.get("promptnode_family"),
        "promptedge_text_present": row.get("promptedge_text_present"),
        "target_forward": row.get("target_forward"),
        "predicted_forward": row.get("predicted_forward"),
        "paper_use": "Safety case: answer-bearing no-edge candidate is blocked after hard-negative augmentation.",
    }


def _lifecycle_cost_case(r309: Dict[str, Any]) -> Dict[str, Any]:
    reference = r309.get("reference", {})
    control = (r309.get("controls") or {}).get("no_lifecycle_prune_disabled", {})
    return {
        "mechanism": "lifecycle_cost_control",
        "source_run": "R309",
        "baseline_forwarded": reference.get("r306_main_forwarded"),
        "no_lifecycle_forwarded": control.get("main_forwarded"),
        "baseline_cost_normalized_correct": reference.get("r306_main_cost_normalized_correct"),
        "no_lifecycle_cost_normalized_correct": control.get("main_cost_normalized_correct"),
        "outcome": "accuracy_ties_but_cost_worse_without_prune",
        "lifecycle_actions": ["compress", "prune"],
        "paper_use": "Efficiency case: lifecycle pruning preserves accuracy while avoiding always-forward cost.",
    }


def build_case_study_summary(
    r306_jsonl: str = DEFAULT_R306_JSONL,
    r309_summary: str = DEFAULT_R309_SUMMARY,
    r327_predictions_jsonl: str = DEFAULT_R327_PREDICTIONS_JSONL,
) -> Dict[str, Any]:
    r306_rows = _load_jsonl(r306_jsonl)
    r327_rows = _load_jsonl(r327_predictions_jsonl)
    r309 = _load_json(r309_summary)
    cases = [
        _verifier_repair_case(r306_rows),
        _memory_bridge_case(r306_rows),
        _promptedge_block_case(r327_rows),
        _lifecycle_cost_case(r309),
    ]
    mechanisms = {case["mechanism"] for case in cases}
    required = {
        "verifier_repair",
        "memory_bridge_prune",
        "promptedge_false_forward_block",
        "lifecycle_cost_control",
    }
    return {
        "run_id": "R329",
        "title": "Case study extraction",
        "claim_boundary": (
            "R329 extracts paper-facing mechanism cases from existing logs. The cases explain the method but do not "
            "change quantitative claims."
        ),
        "no_api": True,
        "broad_api": False,
        "case_studies": cases,
        "paper_case_study_count": len(cases),
        "includes_required_mechanisms": required.issubset(mechanisms),
        "sci_q2_ready": False,
        "next_required_run": "R330_paper_tables_and_figures_plan",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R329 Case Study Extraction",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Mechanism | Source | Outcome | Paper Use |",
        "|---|---|---|---|",
    ]
    for case in summary["case_studies"]:
        rows.append(
            f"| `{case['mechanism']}` | `{case.get('source_run')}` | `{case.get('outcome')}` | {case.get('paper_use')} |"
        )
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r306_jsonl: str = DEFAULT_R306_JSONL,
    r309_summary: str = DEFAULT_R309_SUMMARY,
    r327_predictions_jsonl: str = DEFAULT_R327_PREDICTIONS_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_case_study_summary(
        r306_jsonl=r306_jsonl,
        r309_summary=r309_summary,
        r327_predictions_jsonl=r327_predictions_jsonl,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract R329 paper case studies.")
    parser.add_argument("--r306_jsonl", default=DEFAULT_R306_JSONL)
    parser.add_argument("--r309_summary", default=DEFAULT_R309_SUMMARY)
    parser.add_argument("--r327_predictions_jsonl", default=DEFAULT_R327_PREDICTIONS_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
