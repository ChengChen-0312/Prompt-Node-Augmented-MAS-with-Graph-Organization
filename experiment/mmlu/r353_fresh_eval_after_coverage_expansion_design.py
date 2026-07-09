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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r353_fresh_eval_after_coverage_expansion_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r353_fresh_eval_after_coverage_expansion_design_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def build_fresh_eval_design() -> Dict[str, Any]:
    return {
        "run_id": "R353",
        "title": "Fresh eval after coverage expansion design",
        "claim_boundary": (
            "R353 freezes the expanded R352 PromptNode policy and designs a new fresh MMLU eval. R349/R352 are "
            "excluded because they were used for coverage development."
        ),
        "no_api": True,
        "broad_api": False,
        "policy_frozen_after_run": "R352",
        "fresh_task_plan": {"mmlu_stem": 24, "mmlu_nonstem": 24},
        "exclude_prior_runs": [
            "R304",
            "R306",
            "R312",
            "R334",
            "R337",
            "R341",
            "R342",
            "R346",
            "R347",
            "R349",
            "R352",
        ],
        "planned_variants": ["arg_baseline_direct_api", "expanded_tool_promptnode_local", "hybrid_arg_plus_expanded_tool"],
        "metric_plan": [
            "accuracy",
            "fixes",
            "harms",
            "forwarded_candidate_count",
            "candidate_error_count",
            "token_cost_for_arg_baseline",
            "cost_normalized_accuracy",
        ],
        "api_calls_planned": 48,
        "preflight_required_next": True,
        "api_execution_authorized_next": False,
        "claim_permissions": {
            "fresh_eval_design_allowed": True,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "next_required_run": "R354_fresh_eval_after_coverage_expansion_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R353 Fresh Eval After Coverage Expansion Design",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Policy frozen after: `{summary['policy_frozen_after_run']}`",
        f"- Fresh task plan: `{summary['fresh_task_plan']}`",
        f"- Planned variants: `{summary['planned_variants']}`",
        f"- API calls planned: `{summary['api_calls_planned']}`",
        f"- Next required run: `{summary['next_required_run']}`",
        "",
    ]
    return "\n".join(rows)


def run(summary_json: str = DEFAULT_SUMMARY_JSON, report_md: str = DEFAULT_REPORT_MD) -> Dict[str, Any]:
    summary = build_fresh_eval_design()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R353 fresh eval design after coverage expansion.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
