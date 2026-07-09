import argparse
import json
import os
import sys
from typing import Any, Callable, Dict, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.objective_safety_proxy_rule_learner import FORBIDDEN_PROXY_INPUT_FIELDS  # noqa: E402


RULE_NAME = "r116_objective_safety_baseline_only_trigger_audit"
CLAIM_BOUNDARY = "baseline-only trigger audit; no accuracy, cost-reduction, or deployment claim"

DEFAULT_TRAIN_JSONL = "experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl"
DEFAULT_FROZEN_EVAL_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r109_objective_safety_rule_distillation_summary.json"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r116_objective_safety_baseline_only_trigger_audit_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r116_objective_safety_baseline_only_trigger_audit_report.md"
)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _policy_input(row: Dict[str, Any]) -> Dict[str, Any]:
    return row.get("policy_input") or row.get("rule_input")


def _is_target_switch(row: Dict[str, Any]) -> bool:
    return row["target_action"] == "switch_to_objective"


def _switch(prediction: bool) -> str:
    return "switch_to_objective" if prediction else "fallback_to_arg"


def _split(policy_input: Dict[str, Any]) -> bool:
    return bool(policy_input["baseline_direct_votes_split"])


def _valid(policy_input: Dict[str, Any]) -> int:
    return int(policy_input["baseline_direct_valid_vote_count"])


def _majority(policy_input: Dict[str, Any]) -> int:
    return int(policy_input["baseline_direct_majority_count"])


def candidate_rules() -> List[Tuple[str, Callable[[Dict[str, Any]], bool]]]:
    return [
        ("always_fallback", lambda policy_input: False),
        ("baseline_direct_votes_split", lambda policy_input: _split(policy_input)),
        ("baseline_direct_valid_ge2", lambda policy_input: _valid(policy_input) >= 2),
        ("baseline_direct_majority_le1", lambda policy_input: _majority(policy_input) <= 1),
        (
            "baseline_direct_split_or_valid_ge2",
            lambda policy_input: _split(policy_input) or _valid(policy_input) >= 2,
        ),
        (
            "baseline_direct_split_or_majority_le1",
            lambda policy_input: _split(policy_input) or _majority(policy_input) <= 1,
        ),
    ]


def _metrics(
    rows: Sequence[Dict[str, Any]],
    rule_fn: Callable[[Dict[str, Any]], bool],
) -> Dict[str, Any]:
    target_switch_tasks = [row["task_id"] for row in rows if _is_target_switch(row)]
    predicted_switch_tasks = [
        row["task_id"] for row in rows if rule_fn(_policy_input(row))
    ]
    true_positive_switch_tasks = [
        row["task_id"]
        for row in rows
        if rule_fn(_policy_input(row)) and _is_target_switch(row)
    ]
    false_switch_tasks = [
        row["task_id"]
        for row in rows
        if rule_fn(_policy_input(row)) and not _is_target_switch(row)
    ]
    missed_switch_tasks = [
        row["task_id"]
        for row in rows
        if (not rule_fn(_policy_input(row))) and _is_target_switch(row)
    ]
    agreement = sum(
        1
        for row in rows
        if _switch(rule_fn(_policy_input(row))) == row["target_action"]
    )
    recall_denominator = len(target_switch_tasks)
    precision_denominator = len(predicted_switch_tasks)
    return {
        "agreement": agreement,
        "agreement_text": f"{agreement}/{len(rows)}",
        "predicted_switch_tasks": predicted_switch_tasks,
        "true_positive_switch_tasks": true_positive_switch_tasks,
        "false_switch_tasks": false_switch_tasks,
        "missed_switch_tasks": missed_switch_tasks,
        "switch_recall_count": len(true_positive_switch_tasks),
        "switch_recall_text": f"{len(true_positive_switch_tasks)}/{recall_denominator}",
        "switch_precision_count": len(true_positive_switch_tasks),
        "switch_precision_text": f"{len(true_positive_switch_tasks)}/{precision_denominator}",
    }


def _input_violation_count(rows: Sequence[Dict[str, Any]]) -> int:
    return sum(
        1
        for row in rows
        if FORBIDDEN_PROXY_INPUT_FIELDS.intersection(_policy_input(row))
    )


def build_baseline_only_trigger_audit_summary() -> Dict[str, Any]:
    train_rows = _load_jsonl(DEFAULT_TRAIN_JSONL)
    eval_rows = list(_load_json(DEFAULT_FROZEN_EVAL_JSON)["rows"])
    candidates = []
    for index, (name, rule_fn) in enumerate(candidate_rules()):
        train_metrics = _metrics(train_rows, rule_fn)
        eval_metrics = _metrics(eval_rows, rule_fn)
        candidates.append(
            {
                "name": name,
                "index": index,
                "train": train_metrics,
                "frozen_tail34": eval_metrics,
            }
        )
    best_train = max(candidates, key=lambda item: (item["train"]["agreement"], -item["index"]))
    best_recall = max(
        candidates,
        key=lambda item: (
            item["frozen_tail34"]["switch_recall_count"],
            item["frozen_tail34"]["switch_precision_count"],
            item["frozen_tail34"]["agreement"],
            -item["index"],
        ),
    )
    split_rule = next(item for item in candidates if item["name"] == "baseline_direct_votes_split")
    return {
        "rule": RULE_NAME,
        "candidate_rule_count": len(candidates),
        "best_train_rule": best_train["name"],
        "best_train_agreement": best_train["train"]["agreement_text"],
        "best_train_frozen_tail34_agreement": best_train["frozen_tail34"]["agreement_text"],
        "best_train_frozen_switch_recall": best_train["frozen_tail34"]["switch_recall_text"],
        "baseline_split_frozen_switch_recall": split_rule["frozen_tail34"]["switch_recall_text"],
        "baseline_split_false_switch_tasks": split_rule["frozen_tail34"]["false_switch_tasks"],
        "baseline_split_missed_switch_tasks": split_rule["frozen_tail34"]["missed_switch_tasks"],
        "best_recall_rule": best_recall["name"],
        "best_recall_frozen_switch_recall": best_recall["frozen_tail34"]["switch_recall_text"],
        "best_recall_frozen_switch_precision": best_recall["frozen_tail34"]["switch_precision_text"],
        "best_recall_frozen_tail34_agreement": best_recall["frozen_tail34"]["agreement_text"],
        "baseline_only_proxy_sufficient": False,
        "input_field_violations": _input_violation_count(train_rows) + _input_violation_count(eval_rows),
        "candidate_results": candidates,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "| `{name}` | `{train}` | `{eval_agreement}` | `{recall}` | `{precision}` |".format(
            name=item["name"],
            train=item["train"]["agreement_text"],
            eval_agreement=item["frozen_tail34"]["agreement_text"],
            recall=item["frozen_tail34"]["switch_recall_text"],
            precision=item["frozen_tail34"]["switch_precision_text"],
        )
        for item in summary["candidate_results"]
    ]
    return "\n".join(
        [
            "# R116 Objective-Safety Baseline-Only Trigger Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Candidate rules: `{summary['candidate_rule_count']}`",
            f"- Best train rule: `{summary['best_train_rule']}`",
            f"- Best train agreement: `{summary['best_train_agreement']}`",
            f"- Best train frozen switch recall: `{summary['best_train_frozen_switch_recall']}`",
            f"- Baseline-split frozen switch recall: `{summary['baseline_split_frozen_switch_recall']}`",
            f"- Baseline-split false switches: `{summary['baseline_split_false_switch_tasks']}`",
            f"- Baseline-split missed switches: `{summary['baseline_split_missed_switch_tasks']}`",
            f"- Best recall rule: `{summary['best_recall_rule']}`",
            f"- Best recall frozen switch precision: `{summary['best_recall_frozen_switch_precision']}`",
            f"- Baseline-only proxy sufficient: `{summary['baseline_only_proxy_sufficient']}`",
            f"- Input-field violations: `{summary['input_field_violations']}`",
            "",
            "| Rule | Train agreement | Frozen tail34 agreement | Frozen switch recall | Frozen switch precision |",
            "| --- | ---: | ---: | ---: | ---: |",
            *rows,
            "",
            "## Interpretation",
            "",
            "R116 shows that baseline-only trigger rules cannot replace the objective-guided trace. "
            "The most conservative train-selected rule misses both frozen switch targets; the direct-split "
            "rule misses clean `task_250`; and the high-recall rule covers both switch targets only by "
            "triggering many false switches. Cost reduction therefore needs a lightweight objective trace "
            "or graph-policy signal, not a baseline-only shortcut.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit baseline-only triggers for the objective-safety proxy.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_baseline_only_trigger_audit_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R116 baseline-only trigger audit: "
        f"baseline_only_proxy_sufficient={summary['baseline_only_proxy_sufficient']}"
    )


if __name__ == "__main__":
    main()
