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


DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r348_fresh_tool_promptnode_eval_design_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r348_fresh_tool_promptnode_eval_design_report.md"


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
        "run_id": "R348",
        "title": "Fresh frozen-policy tool PromptNode evaluation design",
        "claim_boundary": (
            "R348 freezes the R345-R347 tool-backed PromptNode policy and designs a fresh MMLU eval that excludes "
            "previously used R334/R337 tasks. It is a protocol design only; no API is executed here."
        ),
        "no_api": True,
        "broad_api": False,
        "policy_frozen_after_run": "R347",
        "frozen_policy_components": [
            "PN_CoordinateTransformer",
            "PN_FiniteAbelianGroupEnumerator",
            "PN_FiniteFieldDerivativeAnalyzer",
            "PN_RedoxBalanceLinearSolver",
            "PromptEdge reject_if_unparsed_or_inconsistent",
            "PromptEdge forward_exact_single_option_match_only",
        ],
        "fresh_task_plan": {"mmlu_stem": 24, "mmlu_nonstem": 24},
        "exclude_prior_runs": ["R304", "R306", "R312", "R334", "R337", "R341", "R342", "R346", "R347"],
        "planned_variants": ["arg_baseline_direct_api", "frozen_tool_promptnode_local", "hybrid_arg_plus_tool"],
        "metric_plan": [
            "accuracy",
            "fixes",
            "harms",
            "clean_fix_harm_if_audit_available",
            "forwarded_candidate_count",
            "token_cost_for_arg_baseline",
            "cost_normalized_accuracy",
        ],
        "api_calls_planned": 48,
        "leakage_preflight_required_next": True,
        "api_execution_authorized_next": False,
        "claim_permissions": {
            "fresh_eval_design_allowed": True,
            "replay_mechanism_evidence_allowed": True,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "next_required_run": "R349_fresh_tool_promptnode_eval_preflight",
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R348 Fresh Tool PromptNode Eval Design",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Policy frozen after: `{summary['policy_frozen_after_run']}`",
        f"- Fresh task plan: `{summary['fresh_task_plan']}`",
        f"- Planned variants: `{summary['planned_variants']}`",
        f"- API calls planned: `{summary['api_calls_planned']}`",
        "",
        "## Frozen Components",
        "",
    ]
    rows.extend(f"- `{component}`" for component in summary["frozen_policy_components"])
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run(summary_json: str = DEFAULT_SUMMARY_JSON, report_md: str = DEFAULT_REPORT_MD) -> Dict[str, Any]:
    summary = build_fresh_eval_design()
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R348 fresh frozen-policy tool PromptNode eval design.")
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
