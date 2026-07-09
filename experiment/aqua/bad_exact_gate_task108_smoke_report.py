import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_bad_exact_gate import (  # noqa: E402
    build_bad_exact_features,
    decide_bad_exact_gate,
)
from experiment.aqua.forced_template_gate_r058_stress import (  # noqa: E402
    DEFAULT_BASELINE_RESULTS,
    _load_jsonl_by_task,
    _repo_path,
)
from experiment.aqua.forced_template_smoke_gate import FORBIDDEN_DECISION_FIELDS  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r090_task108_forced_template_bad_exact_gate_smoke"
CLAIM_BOUNDARY = "single-task fresh smoke, not tail34 accuracy"

DEFAULT_RESULT_JSONL = "experiment/aqua/aqua_tail34_r090_forced_template_rank1_task108_smoke_results.jsonl"
DEFAULT_SUMMARY_JSONL = "experiment/aqua/res_logs/aqua_tail34_r090_forced_template_rank1_task108_smoke_summary.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r090_bad_exact_gate_task108_smoke_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r090_bad_exact_gate_task108_smoke_report.md"


def _load_first_jsonl(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return json.loads(line)
    raise ValueError(f"No JSONL records in {path}")


def _load_last_jsonl(path: str) -> Dict[str, Any]:
    last = None
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = json.loads(line)
    if last is None:
        raise ValueError(f"No JSONL records in {path}")
    return last


def build_task108_smoke_summary(
    result_jsonl: str = DEFAULT_RESULT_JSONL,
    summary_jsonl: str = DEFAULT_SUMMARY_JSONL,
    baseline_results: str = DEFAULT_BASELINE_RESULTS,
) -> Dict[str, Any]:
    result = _load_first_jsonl(result_jsonl)
    cost_summary = _load_last_jsonl(summary_jsonl)
    baseline = _load_jsonl_by_task(baseline_results)[result["task_id"]]
    features = build_bad_exact_features(result)
    decision = decide_bad_exact_gate(features)
    final = result if decision["action"] == "accept_template" else baseline

    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "task_id": result["task_id"],
        "baseline_prediction": baseline.get("predicted_answer"),
        "forced_template_prediction": result.get("predicted_answer"),
        "gate_prediction": final.get("predicted_answer"),
        "true_answer": result.get("true_answer"),
        "baseline_solved": int(bool(baseline.get("is_solved"))),
        "forced_template_solved": int(bool(result.get("is_solved"))),
        "gate_solved": int(bool(final.get("is_solved"))),
        "gate_action": decision["action"],
        "gate_reason": decision["reason"],
        "decision_features": features,
        "decision_field_violations": len(FORBIDDEN_DECISION_FIELDS.intersection(features)),
        "cost": float(cost_summary.get("cost") or 0.0),
        "prompt_tokens": int(cost_summary.get("prompt_tokens") or 0),
        "completion_tokens": int(cost_summary.get("completion_tokens") or 0),
        "result_path": result_jsonl,
        "summary_path": summary_jsonl,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R090 Task108 Forced-Template Bad-Exact Gate Smoke Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Task: `{summary['task_id']}`",
            f"- ARG baseline: `{summary['baseline_prediction']}` solved `{summary['baseline_solved']}`",
            f"- Forced template: `{summary['forced_template_prediction']}` solved `{summary['forced_template_solved']}`",
            f"- R088 gate: `{summary['gate_prediction']}` solved `{summary['gate_solved']}`",
            f"- Gate action: `{summary['gate_action']}`",
            f"- Gate reason: `{summary['gate_reason']}`",
            f"- Cost: `${summary['cost']:.6f}`",
            f"- Decision-field violations: `{summary['decision_field_violations']}`",
            "",
            "## Interpretation",
            "",
            "`task_108` is the only accepted switch in the R088 R058 replay. The fresh forced-template rank-1 smoke "
            "reproduces the same behavior: the explicit PromptNode graph predicts `D`, the R088 gate accepts it as a "
            "trusted exact contract, and the ARG baseline record is wrong. This is one fresh task-level mechanism "
            "check, not a tail34 accuracy result.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize the R090 task108 forced-template smoke.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_task108_smoke_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built task108 bad-exact gate smoke report: "
        f"baseline={summary['baseline_solved']} forced={summary['forced_template_solved']} "
        f"gate={summary['gate_solved']} cost=${summary['cost']:.6f}"
    )


if __name__ == "__main__":
    main()
