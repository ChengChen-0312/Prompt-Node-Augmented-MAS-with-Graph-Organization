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

from experiment.mmlu.r416_cost_normalized_claim_table_and_goal_audit import build_cost_table


DEFAULT_R425 = "experiment/mmlu/res_logs/mmlu_r425_analyze_mmlu_stem_cost_probe_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_report.md"


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


def _stem_probe_row(r425: Dict[str, Any]) -> Dict[str, Any]:
    main_correct, main_total = str(r425.get("main_score")).split("/")
    cost = float(r425.get("estimated_main97_combined_cost"))
    correct = int(main_correct)
    total = int(main_total)
    accuracy = round(correct / total, 6)
    return {
        "id": "MMLU_STEM_R306_probe_estimate",
        "slice": "MMLU_STEM_main97",
        "score": r425.get("main_score"),
        "accuracy": accuracy,
        "cost": cost,
        "cost_per_task": round(cost / total, 6),
        "correct_per_cost": round(correct / cost, 6),
        "accuracy_per_cost": round(accuracy / cost, 6),
        "prompt_tokens": None,
        "completion_tokens": None,
        "fix_harm_wrong": "2/0/n/a",
        "source": DEFAULT_R425,
        "role": "MMLU STEM positive result with probe-estimated cost",
        "note": "Cost is extrapolated from R424 12-task probe; not exact R306 accounting.",
        "cost_evidence": "probe_estimate_not_exact",
    }


def build_updated_cost_table(r425_summary: str = DEFAULT_R425) -> Dict[str, Any]:
    base = build_cost_table()
    r425 = _load_json(r425_summary)
    rows: List[Dict[str, Any]] = []
    for row in base["cost_rows"]:
        if row.get("id") == "MMLU_STEM_R306_cost_missing":
            rows.append(_stem_probe_row(r425))
        else:
            updated = dict(row)
            updated.setdefault("cost_evidence", "direct_or_existing_summary")
            rows.append(updated)
    missing = [item for item in base.get("missing_cost_evidence", []) if item != "MMLU_STEM_cost_missing"]
    if "independent_integrity_audit_missing" not in missing:
        missing.append("independent_integrity_audit_missing")
    return {
        "run_id": "R426",
        "title": "Update cost table with STEM probe and goal audit",
        "claim_boundary": (
            "R426 replaces the missing MMLU STEM cost row with a probe estimate. This improves draft completeness but "
            "does not make submission cost evidence exact or audited."
        ),
        "no_api": True,
        "broad_api": False,
        "cost_rows": rows,
        "missing_cost_evidence": missing,
        "cost_table_complete_for_draft": True,
        "cost_table_complete_for_submission": False,
        "iterations_since_last_goal_check": ["R422", "R423", "R424", "R425", "R426"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "arg_designer_remains_main_baseline": True,
            "promptnode_first_class_boundary_preserved": True,
            "mmlu_stem_cost_gap_reduced": True,
            "estimate_not_misrepresented_as_exact": True,
            "external_audit_still_required": True,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "cost_table_for_draft_allowed": True,
            "cost_table_for_submission_allowed": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R427_external_integrity_audit_refresh",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R426 Update Cost Table With STEM Probe And Goal Audit",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Row | Score | Cost | Evidence | Note |",
        "|---|---:|---:|---|---|",
    ]
    for row in summary["cost_rows"]:
        rows.append(
            f"| `{row['id']}` | `{row['score']}` | `{row['cost']}` | `{row.get('cost_evidence', 'direct_or_existing_summary')}` | {row.get('note', '')} |"
        )
    rows.extend(["", "## Missing Cost Evidence", ""])
    rows.extend(f"- `{item}`" for item in summary["missing_cost_evidence"])
    rows.extend(["", "## Goal Check", ""])
    rows.extend(f"- `{key}`: `{value}`" for key, value in summary["goal_alignment"].items())
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(
    r425_summary: str = DEFAULT_R425,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_updated_cost_table(r425_summary=r425_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update cost table with MMLU STEM cost probe estimate.")
    parser.add_argument("--r425_summary", default=DEFAULT_R425)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
