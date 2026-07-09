from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R337_RESULTS = "experiment/mmlu/run_logs/mmlu_r337_prospective_selector_eval_expand24_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r339_selector_non_switch_failure_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r339_selector_non_switch_failure_analysis_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


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


def build_non_switch_analysis(r337_results: str = DEFAULT_R337_RESULTS) -> Dict[str, Any]:
    rows = _load_jsonl(r337_results)
    selector_rows = [row for row in rows if row.get("control_variant") == "selector_promptnode_promptedge_policy"]
    baseline_rows = [row for row in rows if row.get("control_variant") == "arg_baseline_direct"]
    actions = Counter((row.get("parsed_response") or {}).get("action", "UNKNOWN") for row in selector_rows)
    candidate_types = Counter((row.get("candidate") or {}).get("candidate_type", "none") for row in selector_rows)
    answer_bearing = [
        row
        for row in selector_rows
        if str((row.get("candidate") or {}).get("candidate_label") or "").strip()[:1] in {"A", "B", "C", "D", "E"}
    ]
    baseline_wrong = [row for row in baseline_rows if row.get("is_correct") is False]
    selector_wrong = [row for row in selector_rows if row.get("is_correct") is False]
    switches = [row for row in selector_rows if row.get("predicted_answer") != row.get("baseline_prediction")]
    root_causes = []
    if not answer_bearing:
        root_causes.append("no_answer_bearing_candidates")
    if not switches:
        root_causes.append("over_conservative_switch_contract")
    if candidate_types.get("none", 0) + candidate_types.get("instruction_ambiguity_verifier", 0) == len(selector_rows):
        root_causes.append("candidate_library_does_not_cover_prospective_stem_errors")
    return {
        "run_id": "R339",
        "title": "Selector non-switch failure analysis",
        "claim_boundary": (
            "R339 explains why R337 tied ARG: the selector never switched because the prospective candidate generator "
            "produced no answer-bearing candidates. This analysis blocks more API expansion until candidate generation is fixed."
        ),
        "no_api": True,
        "broad_api": False,
        "selector_action_counts": dict(sorted(actions.items())),
        "selector_switches": len(switches),
        "baseline_wrong_tasks": len(baseline_wrong),
        "selector_wrong_tasks": len(selector_wrong),
        "candidate_type_counts": dict(sorted(candidate_types.items())),
        "answer_bearing_candidate_count": len(answer_bearing),
        "root_causes": root_causes,
        "wrong_task_ids": [row.get("task_id") for row in selector_wrong],
        "api_execution_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R340_answer_bearing_candidate_generator_design",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R339 Selector Non-Switch Failure Analysis",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Selector action counts: `{summary['selector_action_counts']}`",
            f"- Selector switches: `{summary['selector_switches']}`",
            f"- Baseline wrong tasks: `{summary['baseline_wrong_tasks']}`",
            f"- Answer-bearing candidates: `{summary['answer_bearing_candidate_count']}`",
            f"- Candidate type counts: `{summary['candidate_type_counts']}`",
            f"- Root causes: `{summary['root_causes']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r337_results: str = DEFAULT_R337_RESULTS,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_non_switch_analysis(r337_results=r337_results)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R337 selector non-switch failure.")
    parser.add_argument("--r337_results", default=DEFAULT_R337_RESULTS)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
