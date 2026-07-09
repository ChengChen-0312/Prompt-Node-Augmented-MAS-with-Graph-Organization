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


DEFAULT_R400_RESULTS = "experiment/mmlu/run_logs/mmlu_r400_contrastive_verifier_targeted_api_results.jsonl"
DEFAULT_R400_SUMMARY = "experiment/mmlu/res_logs/mmlu_r400_contrastive_verifier_targeted_api_execution_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r401_contrastive_verifier_targeted_analysis_and_goal_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r401_contrastive_verifier_targeted_analysis_and_goal_audit_report.md"


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


def build_targeted_analysis(
    r400_results: str = DEFAULT_R400_RESULTS,
    r400_summary: str = DEFAULT_R400_SUMMARY,
) -> Dict[str, Any]:
    rows = _load_jsonl(r400_results)
    r400 = _load_json(r400_summary)
    contract_pass = [row for row in rows if (row.get("parsed_response") or {}).get("promptedge_contract_pass")]
    inconsistent = [row for row in contract_pass if not row.get("candidate_label")]
    return {
        "run_id": "R401",
        "title": "Contrastive verifier targeted analysis and goal audit",
        "claim_boundary": (
            "R401 analyzes R400 and audits the R397-R400 contrastive branch. The contrastive path failed safely: "
            "it produced no forwarded labels and therefore should not be integrated."
        ),
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "candidate_label_count": sum(1 for row in rows if row.get("candidate_label")),
        "candidate_correct_count": sum(1 for row in rows if row.get("candidate_is_correct")),
        "candidate_repairs_arg_count": sum(1 for row in rows if row.get("candidate_repairs_arg")),
        "candidate_would_harm_arg_count": sum(1 for row in rows if row.get("candidate_would_harm_arg")),
        "contract_pass_count": len(contract_pass),
        "contract_inconsistency_count": len(inconsistent),
        "contract_inconsistency_task_ids": [row.get("task_id") for row in inconsistent],
        "iterations_since_last_goal_check": ["R397", "R398", "R399", "R400"],
        "goal_alignment": {
            "still_aligned_with_sci_q2_goal": True,
            "contrastive_path_failed_safely": len(rows) > 0 and not any(row.get("candidate_label") for row in rows),
            "do_not_integrate_contrastive_path": True,
            "result_to_claim_synthesis_required": True,
            "overclaiming_blocked": True,
        },
        "claim_permissions": {
            "integrate_contrastive_path": False,
            "result_to_claim_synthesis_allowed_next": True,
            "api_execution_allowed_now": False,
            "main_paper_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "api_cost": r400.get("api_cost"),
        "prompt_tokens": r400.get("prompt_tokens"),
        "completion_tokens": r400.get("completion_tokens"),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R402_result_to_claim_synthesis_for_paper",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R401 Contrastive Verifier Targeted Analysis And Goal Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Candidate labels/repairs: `{summary['candidate_label_count']}/{summary['candidate_repairs_arg_count']}`",
            f"- Contract pass/inconsistent: `{summary['contract_pass_count']}/{summary['contract_inconsistency_count']}`",
            f"- Integrate contrastive path: `{summary['claim_permissions']['integrate_contrastive_path']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r400_results: str = DEFAULT_R400_RESULTS,
    r400_summary: str = DEFAULT_R400_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_targeted_analysis(r400_results=r400_results, r400_summary=r400_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R400 contrastive verifier targeted probe and audit goal.")
    parser.add_argument("--r400_results", default=DEFAULT_R400_RESULTS)
    parser.add_argument("--r400_summary", default=DEFAULT_R400_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
