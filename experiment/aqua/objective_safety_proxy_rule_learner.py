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


RULE_NAME = "r113_objective_safety_proxy_rule_learner"
CLAIM_BOUNDARY = "rule-proxy target agreement only; no answer accuracy or prospective API claim"

DEFAULT_TRAIN_JSONL = "experiment/aqua/aqua_first200_r112_objective_safety_feature_targets.jsonl"
DEFAULT_FROZEN_EVAL_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r109_objective_safety_rule_distillation_summary.json"
)
DEFAULT_EVAL_JSONL = "experiment/aqua/aqua_tail34_r113_objective_safety_proxy_rule_eval.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r113_objective_safety_proxy_rule_summary.json"
)
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r113_objective_safety_proxy_rule_report.md"

FORBIDDEN_PROXY_INPUT_FIELDS = {
    "task_id",
    "true_answer",
    "is_solved",
    "baseline_is_solved",
    "objective_selector_is_solved",
    "safety_composed_is_solved",
    "clean_label",
    "audit_label",
    "gold_binding_status",
    "rationale_issue",
    "target_action",
    "target_reason",
}


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


def _write_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _is_switch(prediction: bool) -> str:
    return "switch_to_objective" if prediction else "fallback_to_arg"


def _diff(policy_input: Dict[str, Any]) -> bool:
    return bool(policy_input["objective_prediction_differs_from_baseline"])


def _split(policy_input: Dict[str, Any]) -> bool:
    return bool(policy_input["baseline_direct_votes_split"])


def _score(policy_input: Dict[str, Any]) -> int:
    return int(policy_input["objective_top_score"])


def candidate_rules() -> List[Tuple[str, Callable[[Dict[str, Any]], bool], int]]:
    candidates: List[Tuple[str, Callable[[Dict[str, Any]], bool], int]] = [
        ("always_fallback", lambda policy_input: False, 0),
        ("diff_only", lambda policy_input: _diff(policy_input), 1),
        ("diff_and_split", lambda policy_input: _diff(policy_input) and _split(policy_input), 2),
        ("top_score_ge_3", lambda policy_input: _score(policy_input) >= 3, 1),
    ]
    for threshold in range(1, 7):
        candidates.append(
            (
                f"diff_and_top_score_ge_{threshold}",
                lambda policy_input, threshold=threshold: (
                    _diff(policy_input) and _score(policy_input) >= threshold
                ),
                2,
            )
        )
    for threshold in range(1, 7):
        candidates.append(
            (
                f"diff_and_top_score_ge_{threshold}_or_split",
                lambda policy_input, threshold=threshold: (
                    _diff(policy_input)
                    and (_score(policy_input) >= threshold or _split(policy_input))
                ),
                3,
            )
        )
    return candidates


def _policy_input(row: Dict[str, Any]) -> Dict[str, Any]:
    if "policy_input" in row:
        return row["policy_input"]
    return row["rule_input"]


def _target_action(row: Dict[str, Any]) -> str:
    return row["target_action"]


def _agreement(
    rows: Sequence[Dict[str, Any]],
    rule_fn: Callable[[Dict[str, Any]], bool],
) -> Tuple[int, List[Dict[str, Any]]]:
    predictions = []
    matches = 0
    for row in rows:
        policy_input = _policy_input(row)
        prediction = _is_switch(rule_fn(policy_input))
        target = _target_action(row)
        match = prediction == target
        matches += int(match)
        predictions.append(
            {
                "task_id": row.get("task_id"),
                "target_action": target,
                "proxy_action": prediction,
                "matches_target": match,
            }
        )
    return matches, predictions


def _input_violation_count(rows: Sequence[Dict[str, Any]]) -> int:
    return sum(
        1
        for row in rows
        if FORBIDDEN_PROXY_INPUT_FIELDS.intersection(_policy_input(row))
    )


def _choose_rule(train_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    best: Dict[str, Any] | None = None
    for index, (name, rule_fn, complexity) in enumerate(candidate_rules()):
        matches, _ = _agreement(train_rows, rule_fn)
        score = (matches, -complexity, -index)
        candidate = {
            "name": name,
            "fn": rule_fn,
            "matches": matches,
            "complexity": complexity,
            "index": index,
            "score": score,
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    if best is None:
        raise ValueError("No candidate proxy rules available")
    return best


def build_proxy_rule_summary(
    train_jsonl: str = DEFAULT_TRAIN_JSONL,
    frozen_eval_json: str = DEFAULT_FROZEN_EVAL_JSON,
) -> Dict[str, Any]:
    train_rows = _load_jsonl(train_jsonl)
    frozen_eval = _load_json(frozen_eval_json)
    eval_rows = list(frozen_eval["rows"])
    selected = _choose_rule(train_rows)
    train_matches, train_predictions = _agreement(train_rows, selected["fn"])
    eval_matches, eval_predictions = _agreement(eval_rows, selected["fn"])
    eval_switch_tasks = [
        row["task_id"]
        for row, prediction in zip(eval_rows, eval_predictions)
        if prediction["proxy_action"] == "switch_to_objective"
    ]
    return {
        "rule": RULE_NAME,
        "train_source": train_jsonl,
        "frozen_eval_source": frozen_eval_json,
        "eval_jsonl": DEFAULT_EVAL_JSONL,
        "train_rows": len(train_rows),
        "frozen_eval_rows": len(eval_rows),
        "candidate_rule_count": len(candidate_rules()),
        "learned_rule": selected["name"],
        "learned_rule_complexity": selected["complexity"],
        "train_target_agreement": f"{train_matches}/{len(train_rows)}",
        "train_target_agreement_rate": train_matches / len(train_rows) if train_rows else 0.0,
        "frozen_tail34_target_agreement": f"{eval_matches}/{len(eval_rows)}",
        "frozen_tail34_target_agreement_rate": eval_matches / len(eval_rows) if eval_rows else 0.0,
        "frozen_tail34_switch_tasks": eval_switch_tasks,
        "uses_tail34_training_source": "tail34" in train_jsonl,
        "proxy_input_field_violations": _input_violation_count(train_rows) + _input_violation_count(eval_rows),
        "eval_predictions": eval_predictions,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R113 Objective-Safety Proxy Rule Learner",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Train source: `{summary['train_source']}`",
            f"- Frozen eval source: `{summary['frozen_eval_source']}`",
            f"- Train rows: `{summary['train_rows']}`",
            f"- Frozen eval rows: `{summary['frozen_eval_rows']}`",
            f"- Candidate rules: `{summary['candidate_rule_count']}`",
            f"- Learned rule: `{summary['learned_rule']}`",
            f"- Train target agreement: `{summary['train_target_agreement']}`",
            f"- Frozen tail34 target agreement: `{summary['frozen_tail34_target_agreement']}`",
            f"- Frozen tail34 switch tasks: `{summary['frozen_tail34_switch_tasks']}`",
            f"- Uses tail34 training source: `{summary['uses_tail34_training_source']}`",
            f"- Proxy input-field violations: `{summary['proxy_input_field_violations']}`",
            "",
            "## Interpretation",
            "",
            "R113 fits a compact proxy rule on R112 first200/non-tail34 target rows and evaluates it on "
            "the frozen R109 tail34 targets. This supports target-agreement reproducibility for the "
            "objective-safety rule, but it is not an answer-accuracy result and does not remove the need "
            "for prospective API validation or transfer testing.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fit and evaluate the objective-safety proxy rule.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--eval-jsonl", default=DEFAULT_EVAL_JSONL)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_proxy_rule_summary()
    summary["eval_jsonl"] = args.eval_jsonl
    _write_jsonl(args.eval_jsonl, summary["eval_predictions"])
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R113 objective-safety proxy rule: "
        f"learned={summary['learned_rule']} "
        f"eval={summary['frozen_tail34_target_agreement']}"
    )


if __name__ == "__main__":
    main()
