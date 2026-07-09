from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R424_SUMMARY = "experiment/mmlu/res_logs/mmlu_r424_mmlu_stem_cost_probe_api_execution_summary.json"
DEFAULT_R306_SUMMARY = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r425_analyze_mmlu_stem_cost_probe_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r425_analyze_mmlu_stem_cost_probe_report.md"


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


def build_cost_probe_analysis(
    r424_summary: str = DEFAULT_R424_SUMMARY,
    r306_summary: str = DEFAULT_R306_SUMMARY,
) -> Dict[str, Any]:
    r424 = _load_json(r424_summary)
    r306 = _load_json(r306_summary)
    by_variant = r424.get("by_variant", {})
    arg = by_variant.get("arg_direct_cost_probe", {})
    pn = by_variant.get("promptnode_stack_cost_probe", {})
    probe_tasks = int(r424.get("tasks") or 0)
    main_records = int(r306.get("main_records") or 97)
    main_correct = int(r306.get("main_correct") or 0)
    arg_cost_per_task = float(arg.get("api_cost") or 0.0) / probe_tasks if probe_tasks else 0.0
    pn_cost_per_task = float(pn.get("api_cost") or 0.0) / probe_tasks if probe_tasks else 0.0
    combined_cost_per_task = arg_cost_per_task + pn_cost_per_task
    estimated_baseline_cost = round(arg_cost_per_task * main_records, 6)
    estimated_promptnode_stack_cost = round(pn_cost_per_task * main_records, 6)
    estimated_combined_cost = round(combined_cost_per_task * main_records, 6)
    prompt_tokens_per_task = (
        (int(arg.get("prompt_tokens") or 0) + int(pn.get("prompt_tokens") or 0)) / probe_tasks if probe_tasks else 0.0
    )
    completion_tokens_per_task = (
        (int(arg.get("completion_tokens") or 0) + int(pn.get("completion_tokens") or 0)) / probe_tasks if probe_tasks else 0.0
    )
    return {
        "run_id": "R425",
        "title": "Analyze MMLU STEM cost probe",
        "claim_boundary": (
            "R425 extrapolates MMLU STEM cost from a small probe. It resolves the missing-cost table gap as an estimate, "
            "not as exact R306 accounting or a new accuracy result."
        ),
        "no_api": True,
        "broad_api": False,
        "estimate_kind": "probe_extrapolated",
        "cost_probe_tasks": probe_tasks,
        "api_errors": int(r424.get("api_errors") or 0),
        "main_records": main_records,
        "main_score": f"{main_correct}/{main_records}",
        "arg_direct_cost_per_task": round(arg_cost_per_task, 6),
        "promptnode_stack_cost_per_task": round(pn_cost_per_task, 6),
        "combined_cost_per_task": round(combined_cost_per_task, 6),
        "estimated_main97_arg_direct_cost": estimated_baseline_cost,
        "estimated_main97_promptnode_stack_cost": estimated_promptnode_stack_cost,
        "estimated_main97_combined_cost": estimated_combined_cost,
        "estimated_prompt_tokens_per_task": round(prompt_tokens_per_task, 3),
        "estimated_completion_tokens_per_task": round(completion_tokens_per_task, 3),
        "estimated_cost_per_correct": round(estimated_combined_cost / main_correct, 6) if main_correct else None,
        "mmlu_stem_cost_gap_status": "resolved_as_estimate_not_exact",
        "accuracy_claim_from_probe_authorized": False,
        "cost_estimate_allowed_for_table": True,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R426_update_cost_table_with_stem_probe_and_goal_audit",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R425 Analyze MMLU STEM Cost Probe",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Probe tasks/errors: `{summary['cost_probe_tasks']}/{summary['api_errors']}`",
            f"- Main score: `{summary['main_score']}`",
            f"- Cost per task ARG/PN/combined: `{summary['arg_direct_cost_per_task']}/{summary['promptnode_stack_cost_per_task']}/{summary['combined_cost_per_task']}`",
            f"- Estimated main97 combined cost: `{summary['estimated_main97_combined_cost']}`",
            f"- Gap status: `{summary['mmlu_stem_cost_gap_status']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r424_summary: str = DEFAULT_R424_SUMMARY,
    r306_summary: str = DEFAULT_R306_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_cost_probe_analysis(r424_summary=r424_summary, r306_summary=r306_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze MMLU STEM cost probe.")
    parser.add_argument("--r424_summary", default=DEFAULT_R424_SUMMARY)
    parser.add_argument("--r306_summary", default=DEFAULT_R306_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
