import argparse
import json
import os
import sys
from typing import Any, Callable, Dict, List, Sequence


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.objective_safety_proxy_rule_learner import (  # noqa: E402
    FORBIDDEN_PROXY_INPUT_FIELDS,
    candidate_rules,
)


RULE_NAME = "r114_objective_safety_proxy_regression_stress"
CLAIM_BOUNDARY = (
    "four-task regression replay of R113 over R106/R107 traces; "
    "no new API or held-out accuracy claim"
)

DEFAULT_R113_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r113_objective_safety_proxy_rule_summary.json"
)
DEFAULT_R107_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r107_objective_safety_rank5_guard_summary.json"
)
DEFAULT_STRESS_JSONL = "experiment/aqua/aqua_tail34_r114_objective_safety_proxy_regression_stress.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r114_objective_safety_proxy_regression_stress_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r114_objective_safety_proxy_regression_stress_report.md"
)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _write_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _rule_fn(rule_name: str) -> Callable[[Dict[str, Any]], bool]:
    for name, fn, _complexity in candidate_rules():
        if name == rule_name:
            return fn
    raise ValueError(f"Unknown learned proxy rule: {rule_name}")


def _proxy_action(rule_fn: Callable[[Dict[str, Any]], bool], selector_inputs: Dict[str, Any]) -> str:
    return "accept_rank5" if rule_fn(selector_inputs) else "fallback_to_arg"


def _fix_harm(rows: Sequence[Dict[str, Any]]) -> str:
    return f"{sum(1 for row in rows if row['fix'])}/{sum(1 for row in rows if row['harm'])}"


def _input_violation_count(rows: Sequence[Dict[str, Any]]) -> int:
    return sum(
        1
        for row in rows
        if FORBIDDEN_PROXY_INPUT_FIELDS.intersection(row["selector_inputs"])
    )


def build_proxy_regression_stress_rows(
    r113_summary_json: str = DEFAULT_R113_SUMMARY_JSON,
    r107_summary_json: str = DEFAULT_R107_SUMMARY_JSON,
) -> List[Dict[str, Any]]:
    r113 = _load_json(r113_summary_json)
    r107 = _load_json(r107_summary_json)
    rule_fn = _rule_fn(r113["learned_rule"])
    rows = []
    for row in r107["rows"]:
        action = _proxy_action(rule_fn, row["selector_inputs"])
        guarded_prediction = (
            row["rank5_prediction"] if action == "accept_rank5" else row["baseline_prediction"]
        )
        guarded_is_solved = guarded_prediction == row["true_answer"]
        fix = (not row["baseline_is_solved"]) and guarded_is_solved
        harm = row["baseline_is_solved"] and not guarded_is_solved
        rows.append(
            {
                "task_id": row["task_id"],
                "selector_inputs": row["selector_inputs"],
                "r107_action": row["action"],
                "proxy_action": action,
                "matches_r107_action": action == row["action"],
                "baseline_prediction": row["baseline_prediction"],
                "rank5_prediction": row["rank5_prediction"],
                "proxy_guarded_prediction": guarded_prediction,
                "true_answer": row["true_answer"],
                "baseline_is_solved": row["baseline_is_solved"],
                "rank5_is_solved": row["rank5_is_solved"],
                "proxy_guarded_is_solved": guarded_is_solved,
                "rank5_harm": row["rank5_harm"],
                "fix": fix,
                "harm": harm,
                "clean_label": row["clean_label"],
            }
        )
    return rows


def build_proxy_regression_stress_summary() -> Dict[str, Any]:
    r113 = _load_json(DEFAULT_R113_SUMMARY_JSON)
    rows = build_proxy_regression_stress_rows()
    clean_rows = [row for row in rows if row["clean_label"] == "clean"]
    noisy_rows = [row for row in rows if row["clean_label"] != "clean"]
    action_matches = sum(1 for row in rows if row["matches_r107_action"])
    return {
        "rule": RULE_NAME,
        "learned_rule": r113["learned_rule"],
        "num_tasks": len(rows),
        "proxy_action_agreement_with_r107": f"{action_matches}/{len(rows)}",
        "baseline_solved": sum(1 for row in rows if row["baseline_is_solved"]),
        "rank5_solved": sum(1 for row in rows if row["rank5_is_solved"]),
        "proxy_guarded_solved": sum(1 for row in rows if row["proxy_guarded_is_solved"]),
        "proxy_switch_tasks": [row["task_id"] for row in rows if row["proxy_action"] == "accept_rank5"],
        "proxy_fallback_tasks": [
            row["task_id"] for row in rows if row["proxy_action"] == "fallback_to_arg"
        ],
        "suppressed_rank5_harm_tasks": [
            row["task_id"]
            for row in rows
            if row["rank5_harm"] and row["proxy_action"] == "fallback_to_arg"
        ],
        "clean_recovery_tasks": [
            row["task_id"]
            for row in clean_rows
            if (not row["baseline_is_solved"]) and row["proxy_guarded_is_solved"]
        ],
        "proxy_fix_harm": _fix_harm(rows),
        "proxy_clean_fix_harm": _fix_harm(clean_rows),
        "proxy_noisy_fix_harm": _fix_harm(noisy_rows),
        "proxy_input_field_violations": _input_violation_count(rows),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{label}` | `{action}` | `{base}` | `{rank5}` | `{guarded}` | `{truth}` | `{fix}` | `{harm}` |".format(
            task=row["task_id"],
            label=row["clean_label"],
            action=row["proxy_action"],
            base=row["baseline_prediction"],
            rank5=row["rank5_prediction"],
            guarded=row["proxy_guarded_prediction"],
            truth=row["true_answer"],
            fix=row["fix"],
            harm=row["harm"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R114 Objective-Safety Proxy Regression Stress",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Learned rule: `{summary['learned_rule']}`",
            f"- Tasks: `{summary['num_tasks']}`",
            f"- Proxy action agreement with R107: `{summary['proxy_action_agreement_with_r107']}`",
            f"- Baseline solved: `{summary['baseline_solved']}/{summary['num_tasks']}`",
            f"- Rank5 solved: `{summary['rank5_solved']}/{summary['num_tasks']}`",
            f"- Proxy guarded solved: `{summary['proxy_guarded_solved']}/{summary['num_tasks']}`",
            f"- Proxy switch tasks: `{summary['proxy_switch_tasks']}`",
            f"- Proxy fallback tasks: `{summary['proxy_fallback_tasks']}`",
            f"- Suppressed rank5 harms: `{summary['suppressed_rank5_harm_tasks']}`",
            f"- Clean recovery tasks: `{summary['clean_recovery_tasks']}`",
            f"- Proxy fix/harm: `{summary['proxy_fix_harm']}`",
            f"- Proxy clean fix/harm: `{summary['proxy_clean_fix_harm']}`",
            f"- Proxy noisy fix/harm: `{summary['proxy_noisy_fix_harm']}`",
            f"- Proxy input-field violations: `{summary['proxy_input_field_violations']}`",
            "",
            "| Task | Label | Proxy action | ARG | Rank5 | Proxy guarded | Truth | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R114 checks that the R113 proxy reproduces the known R107 clean-harm/recovery behavior "
            "on the four-task regression set. It is a replay over existing traces, not a new API result "
            "and not a broad held-out accuracy claim.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stress-test the R113 proxy on regression traces.")
    parser.add_argument("--stress-jsonl", default=DEFAULT_STRESS_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_proxy_regression_stress_summary()
    _write_jsonl(args.stress_jsonl, summary["rows"])
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R114 objective-safety proxy regression stress: "
        f"agreement={summary['proxy_action_agreement_with_r107']} "
        f"guarded={summary['proxy_guarded_solved']}/{summary['num_tasks']}"
    )


if __name__ == "__main__":
    main()
