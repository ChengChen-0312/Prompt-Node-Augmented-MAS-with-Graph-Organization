from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_BASELINE_ROWS = "experiment/mmlu/run_logs/mmlu_r292_arg_retrain_first24_api_results.jsonl"
DEFAULT_PROMPTNODE_ROWS = "experiment/mmlu/run_logs/mmlu_r291_constrained_graph_api_full24_all_exposure_results.jsonl"
DEFAULT_SUMMARY = "experiment/mmlu/res_logs/mmlu_r293_failure_analysis_terminal_router_harms_summary.json"
DEFAULT_REPORT = "experiment/mmlu/run_logs/mmlu_r293_failure_analysis_terminal_router_harms_report.md"

SPECIALIST_ROLES = {"Mathematician", "Programmer", "Knowlegable Expert"}


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        f.write(text)


def _task_id(row: Dict[str, Any]) -> str:
    return str(row.get("task_id") or row.get("id"))


def _specialist_count(row: Dict[str, Any]) -> int:
    return sum(1 for role in row.get("roles", []) or [] if role in SPECIALIST_ROLES)


def analyze_harms(
    baseline_rows: List[Dict[str, Any]],
    promptnode_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    baseline_by_id = {_task_id(row): row for row in baseline_rows}
    harms = []
    fixes = []
    for pn in promptnode_rows:
        base = baseline_by_id.get(_task_id(pn))
        if not base:
            continue
        if base.get("is_correct") and not pn.get("is_correct"):
            harms.append({"promptnode": pn, "baseline": base})
        if not base.get("is_correct") and pn.get("is_correct"):
            fixes.append({"promptnode": pn, "baseline": base})

    harm_records = []
    for item in harms:
        pn = item["promptnode"]
        base = item["baseline"]
        pn_specialists = _specialist_count(pn)
        base_specialists = _specialist_count(base)
        harm_records.append(
            {
                "task_id": _task_id(pn),
                "subject": pn.get("subject"),
                "baseline_prediction": base.get("predicted_answer"),
                "promptnode_prediction": pn.get("predicted_answer"),
                "true_answer": pn.get("true_answer"),
                "baseline_roles": base.get("roles", []),
                "promptnode_roles": pn.get("roles", []),
                "baseline_specialist_roles": base_specialists,
                "promptnode_specialist_roles": pn_specialists,
                "specialist_role_loss": pn_specialists < base_specialists,
                "promptnode_contract_ready": pn.get("promptedge_contract_ready"),
            }
        )

    promptnode_role_counts = Counter(
        role for row in promptnode_rows for role in (row.get("roles", []) or [])
    )
    baseline_role_counts = Counter(
        role for row in baseline_rows for role in (row.get("roles", []) or [])
    )
    return {
        "run_id": "R293",
        "title": "Failure analysis for constrained PromptNode transfer harms",
        "claim_boundary": (
            "Offline failure analysis only. It explains observed R291 harms and does not "
            "support a transfer improvement claim."
        ),
        "no_api": True,
        "broad_api": False,
        "matched_tasks": len([row for row in promptnode_rows if _task_id(row) in baseline_by_id]),
        "fixes": len(fixes),
        "harms": len(harms),
        "harms_with_specialist_role_loss": sum(
            1 for row in harm_records if row["specialist_role_loss"]
        ),
        "harm_records": harm_records,
        "baseline_role_counts": dict(sorted(baseline_role_counts.items())),
        "promptnode_role_counts": dict(sorted(promptnode_role_counts.items())),
        "mechanism_hypothesis": (
            "The constrained decoder optimizes for PN chain completeness but not task-specialist "
            "coverage. On harms, selected graphs can replace Mathematician/Programmer/Knowlegable "
            "Expert evidence with Historian-heavy PN chains, causing the router to preserve a "
            "well-structured but wrong contract."
        ),
        "transfer_claim_supported": False,
        "next_action": (
            "Revise graph selection/training objective to jointly require PN contract structure "
            "and specialist-role preservation before running more API."
        ),
    }


def render_report(summary: Dict[str, Any]) -> str:
    harm_rows = [
        f"| `{row['task_id']}` | `{row['subject']}` | `{row['baseline_prediction']}` | `{row['promptnode_prediction']}` | `{row['true_answer']}` | `{row['baseline_specialist_roles']}` -> `{row['promptnode_specialist_roles']}` |"
        for row in summary["harm_records"]
    ]
    return "\n".join(
        [
            "# R293 Failure Analysis: PromptNode Transfer Harms",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Matched tasks: `{summary['matched_tasks']}`",
            f"- Fix/harm: `{summary['fixes']}/{summary['harms']}`",
            f"- Harms with specialist role loss: `{summary['harms_with_specialist_role_loss']}`",
            f"- Transfer claim supported: `{summary['transfer_claim_supported']}`",
            "",
            "## Harm Records",
            "",
            "| Task | Subject | ARG | PromptNode | Truth | Specialist roles |",
            "|---|---|---:|---:|---:|---:|",
            *harm_rows,
            "",
            "## Mechanism Hypothesis",
            "",
            summary["mechanism_hypothesis"],
            "",
            "## Next",
            "",
            summary["next_action"],
            "",
        ]
    )


def run(
    baseline_rows_jsonl: str = DEFAULT_BASELINE_ROWS,
    promptnode_rows_jsonl: str = DEFAULT_PROMPTNODE_ROWS,
    summary_json: str = DEFAULT_SUMMARY,
    report_md: str = DEFAULT_REPORT,
) -> Dict[str, Any]:
    summary = analyze_harms(
        baseline_rows=_load_jsonl(baseline_rows_jsonl),
        promptnode_rows=_load_jsonl(promptnode_rows_jsonl),
    )
    summary.update(
        {
            "source_files": {
                "baseline_rows": baseline_rows_jsonl,
                "promptnode_rows": promptnode_rows_jsonl,
            },
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R293 PromptNode harm failure analysis.")
    parser.add_argument("--baseline_rows_jsonl", default=DEFAULT_BASELINE_ROWS)
    parser.add_argument("--promptnode_rows_jsonl", default=DEFAULT_PROMPTNODE_ROWS)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY)
    parser.add_argument("--report_md", default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
