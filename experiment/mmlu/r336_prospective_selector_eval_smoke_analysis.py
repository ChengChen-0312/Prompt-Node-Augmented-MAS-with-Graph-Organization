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


DEFAULT_R335_SUMMARY = "experiment/mmlu/res_logs/mmlu_r335_prospective_selector_eval_api_smoke_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r336_prospective_selector_eval_smoke_analysis_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r336_prospective_selector_eval_smoke_analysis_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _fix_harm(item: Dict[str, Any]) -> str:
    return f"{int(item.get('fixes', 0))}/{int(item.get('harms', 0))}"


def build_smoke_analysis(r335_summary: str = DEFAULT_R335_SUMMARY) -> Dict[str, Any]:
    r335 = _load_json(r335_summary)
    variants = r335.get("by_variant", {})
    arg = variants.get("arg_baseline_direct", {})
    selector = variants.get("selector_promptnode_promptedge_policy", {})
    plain = variants.get("cost_matched_plain_requery", {})
    selector_delta = int(selector.get("correct", 0)) - int(arg.get("correct", 0))
    plain_delta = int(plain.get("correct", 0)) - int(arg.get("correct", 0))
    return {
        "run_id": "R336",
        "title": "Prospective selector eval smoke analysis",
        "claim_boundary": (
            "R336 analyzes the 6-task API smoke. It supports only selector no-harm on the smoke and a plain-requery "
            "harm control; it does not support a prospective improvement claim."
        ),
        "no_api": True,
        "broad_api": False,
        "source_run": "R335",
        "selector_vs_arg": {
            "arg": f"{arg.get('correct', 0)}/{arg.get('evaluated_records', 0)}",
            "selector": f"{selector.get('correct', 0)}/{selector.get('evaluated_records', 0)}",
            "delta_correct": selector_delta,
            "fix_harm": _fix_harm(selector),
        },
        "plain_requery_vs_arg": {
            "arg": f"{arg.get('correct', 0)}/{arg.get('evaluated_records', 0)}",
            "plain_requery": f"{plain.get('correct', 0)}/{plain.get('evaluated_records', 0)}",
            "delta_correct": plain_delta,
            "fix_harm": _fix_harm(plain),
        },
        "api_cost": r335.get("api_cost"),
        "claim_permissions": {
            "selector_no_harm_smoke_allowed": selector_delta == 0 and int(selector.get("harms", 0)) == 0,
            "selector_improvement_claim_allowed": selector_delta > 0,
            "plain_requery_harm_control_allowed": int(plain.get("harms", 0)) > 0,
            "full_prospective_claim_allowed": False,
            "sci_q2_ready": False,
        },
        "expand_authorized_next": r335.get("api_errors", 1) == 0 and selector_delta >= 0,
        "next_required_run": "R337_prospective_selector_eval_expand24",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R336 Prospective Selector Eval Smoke Analysis",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Selector vs ARG: `{summary['selector_vs_arg']}`",
            f"- Plain requery vs ARG: `{summary['plain_requery_vs_arg']}`",
            f"- Claim permissions: `{summary['claim_permissions']}`",
            f"- Expand authorized next: `{summary['expand_authorized_next']}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    r335_summary: str = DEFAULT_R335_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_smoke_analysis(r335_summary=r335_summary)
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze R335 prospective selector API smoke.")
    parser.add_argument("--r335_summary", default=DEFAULT_R335_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
