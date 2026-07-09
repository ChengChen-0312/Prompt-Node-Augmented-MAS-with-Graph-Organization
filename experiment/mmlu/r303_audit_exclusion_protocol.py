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

from experiment.mmlu.r300_goal_and_label_audit import audit_clean_answer
from experiment.mmlu.r301_conservative_census_gate import load_jsonl, normalize_label


DEFAULT_ARG_RESULTS = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r303_audit_exclusion_protocol_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r303_audit_exclusion_protocol_report.md"

EXCLUDED_TASK_IDS = {
    "MMLU-high_school_statistics_test-32",
    "MMLU-high_school_physics_test-67",
    "MMLU-college_chemistry_test-62",
}

EXCLUSION_REASONS = {
    "MMLU-high_school_statistics_test-32": "Known ARG failure already used for R301/R302 gate discovery; exclude from further training/distillation to avoid tuning to a single audited item.",
    "MMLU-high_school_physics_test-67": "MMLU-Redux 2.0 marks wrong_groundtruth; keep in appendix sensitivity analysis only.",
    "MMLU-college_chemistry_test-62": "MMLU-Redux 2.0 marks wrong_groundtruth; keep in appendix sensitivity analysis only.",
}


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _count_official_correct(rows: Iterable[Dict[str, Any]]) -> int:
    return sum(1 for row in rows if bool(row.get("is_correct")))


def _count_audit_clean_correct(rows: Iterable[Dict[str, Any]]) -> int:
    total = 0
    for row in rows:
        pred = normalize_label(row.get("predicted_answer"))
        clean = audit_clean_answer(str(row.get("task_id") or ""), row.get("true_answer"))
        if pred == clean:
            total += 1
    return total


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_exclusion_summary(arg_results_jsonl: str = DEFAULT_ARG_RESULTS) -> Dict[str, Any]:
    rows = load_jsonl(arg_results_jsonl)
    main_rows = [row for row in rows if str(row.get("task_id") or "") not in EXCLUDED_TASK_IDS]
    appendix_rows = [row for row in rows if str(row.get("task_id") or "") in EXCLUDED_TASK_IDS]
    return {
        "run_id": "R303",
        "title": "MMLU audit-excluded protocol freeze",
        "claim_boundary": (
            "Protocol freeze only. The three audited tasks are excluded from future training/distillation and main-result "
            "aggregation; they remain available for appendix sensitivity analysis."
        ),
        "no_api": True,
        "broad_api": False,
        "arg_results_jsonl": arg_results_jsonl,
        "total_records": len(rows),
        "excluded_count": len(EXCLUDED_TASK_IDS),
        "excluded_task_ids": sorted(EXCLUDED_TASK_IDS),
        "exclusion_reasons": EXCLUSION_REASONS,
        "main_eval_records": len(main_rows),
        "appendix_records": len(appendix_rows),
        "arg_full_official_correct": _count_official_correct(rows),
        "arg_full_audit_clean_correct": _count_audit_clean_correct(rows),
        "arg_main_official_correct": _count_official_correct(main_rows),
        "arg_main_audit_clean_correct": _count_audit_clean_correct(main_rows),
        "arg_appendix_official_correct": _count_official_correct(appendix_rows),
        "arg_appendix_audit_clean_correct": _count_audit_clean_correct(appendix_rows),
        "training_policy": {
            "exclude_from_training": sorted(EXCLUDED_TASK_IDS),
            "exclude_from_distillation": sorted(EXCLUDED_TASK_IDS),
            "main_text_reporting": "Use main97 as the primary MMLU transfer result; report official/audit-clean/full100 in appendix.",
            "appendix_reporting": "Explain one known ARG-discovery item and two MMLU-Redux wrong-groundtruth items.",
        },
        "next_run": "R304 multi-trigger learned SafetyGatePN on main97",
        "sci_q2_ready": False,
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R303 MMLU Audit-Excluded Protocol",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Full ARG official/audit-clean: `{summary['arg_full_official_correct']}/{summary['total_records']}` / `{summary['arg_full_audit_clean_correct']}/{summary['total_records']}`",
        f"- Main ARG official/audit-clean: `{summary['arg_main_official_correct']}/{summary['main_eval_records']}` / `{summary['arg_main_audit_clean_correct']}/{summary['main_eval_records']}`",
        f"- Appendix records: `{summary['appendix_records']}`",
        "",
        "## Excluded Tasks",
        "",
        "| Task | Reason |",
        "| --- | --- |",
    ]
    for task_id in summary["excluded_task_ids"]:
        rows.append(f"| `{task_id}` | {summary['exclusion_reasons'][task_id]} |")
    rows.extend(
        [
            "",
            "## Policy",
            "",
            "The main MMLU transfer result should be computed on the remaining 97 tasks. The excluded tasks should be discussed in an appendix label-audit section, mirroring the AQuA noisy-item treatment.",
            "",
        ]
    )
    return "\n".join(rows)


def run(
    arg_results_jsonl: str = DEFAULT_ARG_RESULTS,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_exclusion_summary(arg_results_jsonl)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze R303 MMLU audit-excluded protocol.")
    parser.add_argument("--arg_results_jsonl", default=DEFAULT_ARG_RESULTS)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
