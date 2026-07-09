from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402


RULE_NAME = "r168_promptedge_selector"

FEATURE_NAMES = [
    "bias",
    "score_margin_to_next",
    "has_margin_at_least_3",
    "objective_bucket_preferred_graph",
    "objective_bucket_multi_view_tie",
    "objective_bucket_low_margin_top",
    "objective_bucket_non_positive_top",
    "objective_bucket_non_preferred_graph",
    "objective_prediction_differs_from_baseline",
    "baseline_direct_votes_split",
    "objective_top_score",
    "num_prompt_nodes",
    "num_prompt_node_edges",
    "has_promptnode_specs",
    "has_promptnode_edge_permissions",
    "role_count_PN_Memory",
    "role_count_PN_Verifier",
    "role_count_PN_Router",
]

FORBIDDEN_INPUT_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "task_id",
    "source_task_id",
}


def _field_violates(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key in FORBIDDEN_INPUT_FIELDS or _field_violates(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_field_violates(child) for child in value)
    return False


def input_field_violations(rows: Sequence[Dict[str, Any]]) -> int:
    return sum(1 for row in rows if _field_violates(row.get("selector_policy_input") or {}))


def _float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def feature_vector(row: Dict[str, Any]) -> List[float]:
    policy_input = row.get("selector_policy_input") or {}
    graph = policy_input.get("candidate_graph_observation") or {}
    role_counts = graph.get("prompt_node_role_counts") or {}
    objective_bucket = str(policy_input.get("objective_bucket") or "")
    values = {
        "bias": 1.0,
        "score_margin_to_next": _float(policy_input.get("score_margin_to_next")),
        "has_margin_at_least_3": _float(policy_input.get("has_margin_at_least_3")),
        "objective_bucket_preferred_graph": 1.0 if objective_bucket == "preferred_graph" else 0.0,
        "objective_bucket_multi_view_tie": 1.0 if objective_bucket == "multi_view_tie" else 0.0,
        "objective_bucket_low_margin_top": 1.0 if objective_bucket == "low_margin_top" else 0.0,
        "objective_bucket_non_positive_top": 1.0 if objective_bucket == "non_positive_top" else 0.0,
        "objective_bucket_non_preferred_graph": 1.0 if objective_bucket == "non_preferred_graph" else 0.0,
        "objective_prediction_differs_from_baseline": _float(
            policy_input.get("objective_prediction_differs_from_baseline")
        ),
        "baseline_direct_votes_split": _float(policy_input.get("baseline_direct_votes_split")),
        "objective_top_score": _float(policy_input.get("objective_top_score")),
        "num_prompt_nodes": _float(graph.get("num_prompt_nodes")),
        "num_prompt_node_edges": _float(graph.get("num_prompt_node_edges")),
        "has_promptnode_specs": _float(graph.get("has_promptnode_specs")),
        "has_promptnode_edge_permissions": _float(graph.get("has_promptnode_edge_permissions")),
        "role_count_PN_Memory": _float(role_counts.get("PN_Memory")),
        "role_count_PN_Verifier": _float(role_counts.get("PN_Verifier")),
        "role_count_PN_Router": _float(role_counts.get("PN_Router")),
    }
    return [values[name] for name in FEATURE_NAMES]


def target_label(row: Dict[str, Any]) -> int:
    return 1 if row.get("positive_graph_target") else 0


def _dot(weights: Sequence[float], features: Sequence[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, features))


def train_selector(
    rows: Sequence[Dict[str, Any]],
    epochs: int = 10,
    learning_rate: float = 0.05,
) -> Dict[str, Any]:
    weights = [0.0 for _ in FEATURE_NAMES]
    updates = 0
    for _ in range(epochs):
        for row in rows:
            features = feature_vector(row)
            gold = 1 if target_label(row) else -1
            if gold * _dot(weights, features) <= 0:
                weights = [
                    weight + learning_rate * gold * value
                    for weight, value in zip(weights, features)
                ]
                updates += 1
    positive_scores = [
        _dot(weights, feature_vector(row))
        for row in rows
        if target_label(row) == 1
    ]
    negative_scores = [
        _dot(weights, feature_vector(row))
        for row in rows
        if target_label(row) == 0
    ]
    if positive_scores and negative_scores and min(positive_scores) > max(negative_scores):
        threshold = (min(positive_scores) + max(negative_scores)) / 2.0
        threshold_policy = "midpoint_between_train_positive_min_and_negative_max"
    else:
        threshold = 0.0
        threshold_policy = "zero_threshold_nonseparable_train_scores"
    return {
        "feature_names": FEATURE_NAMES,
        "weights": {name: weights[index] for index, name in enumerate(FEATURE_NAMES)},
        "threshold": threshold,
        "threshold_policy": threshold_policy,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "updates": updates,
        "claim_boundary": (
            "Selector trained on R166 expanded PromptNode/PromptEdge targets. "
            "Agreement is target agreement, not answer accuracy."
        ),
    }


def _weight_vector(model: Dict[str, Any]) -> List[float]:
    weights = model.get("weights") or {}
    return [float(weights.get(name, 0.0)) for name in FEATURE_NAMES]


def predict_score(model: Dict[str, Any], row: Dict[str, Any]) -> float:
    return _dot(_weight_vector(model), feature_vector(row))


def predict_label(model: Dict[str, Any], row: Dict[str, Any]) -> int:
    threshold = float(model.get("threshold", 0.0))
    return 1 if predict_score(model, row) > threshold else 0


def evaluate_selector(model: Dict[str, Any], rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    tp = fp = tn = fn = 0
    scores: List[float] = []
    for row in rows:
        gold = target_label(row)
        pred = predict_label(model, row)
        scores.append(predict_score(model, row))
        if gold == 1 and pred == 1:
            tp += 1
        elif gold == 0 and pred == 1:
            fp += 1
        elif gold == 0 and pred == 0:
            tn += 1
        else:
            fn += 1
    correct = tp + tn
    predicted_positive = tp + fp
    positive_total = tp + fn
    precision = tp / predicted_positive if predicted_positive else 0.0
    recall = tp / positive_total if positive_total else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "positive_total": positive_total,
        "predicted_positive": predicted_positive,
        "positive_precision": precision,
        "positive_recall": recall,
        "positive_f1": f1,
        "mean_score": sum(scores) / total if total else 0.0,
        "min_score": min(scores) if scores else 0.0,
        "max_score": max(scores) if scores else 0.0,
    }


def split_rows_by_slice(
    rows: Sequence[Dict[str, Any]],
    train_slice: str = "aqua_100",
    eval_slice: str = "aqua_next100",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    train_rows = [row for row in rows if row.get("source_slice_prefix") == train_slice]
    eval_rows = [row for row in rows if row.get("source_slice_prefix") == eval_slice]
    return train_rows, eval_rows


def _target_counts(rows: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = Counter(str(row.get("selective_action")) for row in rows)
    return dict(sorted(counts.items()))


def build_selector_summary(
    rows: Sequence[Dict[str, Any]],
    train_slice: str = "aqua_100",
    eval_slice: str = "aqua_next100",
    epochs: int = 10,
    learning_rate: float = 0.05,
) -> Dict[str, Any]:
    train_rows, eval_rows = split_rows_by_slice(rows, train_slice=train_slice, eval_slice=eval_slice)
    model = train_selector(train_rows, epochs=epochs, learning_rate=learning_rate)
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "source_rows": len(rows),
        "train_slice": train_slice,
        "eval_slice": eval_slice,
        "train_rows": len(train_rows),
        "eval_rows": len(eval_rows),
        "source_target_counts": _target_counts(rows),
        "train_target_counts": _target_counts(train_rows),
        "eval_target_counts": _target_counts(eval_rows),
        "feature_names": FEATURE_NAMES,
        "model": model,
        "train_metrics": evaluate_selector(model, train_rows),
        "eval_metrics": evaluate_selector(model, eval_rows),
        "input_field_violations": input_field_violations(rows),
        "excluded_input_fields": sorted(FORBIDDEN_INPUT_FIELDS),
        "claim_boundary": (
            "R168 trains a lightweight selector over R166 PromptNode/PromptEdge targets. "
            "It reports target agreement only, not AQuA answer accuracy."
        ),
    }


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _format_counts(counts: Dict[str, int]) -> str:
    return ", ".join(f"{key}={value}" for key, value in counts.items()) or "none"


def _format_weights(model: Dict[str, Any]) -> List[str]:
    weights = model.get("weights") or {}
    return [f"| `{name}` | `{float(weights.get(name, 0.0)):.4f}` |" for name in FEATURE_NAMES]


def render_report(summary: Dict[str, Any]) -> str:
    train = summary["train_metrics"]
    eval_metrics = summary["eval_metrics"]
    return "\n".join(
        [
            "# R168 PromptEdge Selector",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Source rows: `{summary['source_rows']}`",
            f"- Train slice: `{summary['train_slice']}` with `{summary['train_rows']}` rows",
            f"- Eval slice: `{summary['eval_slice']}` with `{summary['eval_rows']}` rows",
            f"- Train target agreement: `{train['accuracy']:.3f}`",
            f"- Eval target agreement: `{eval_metrics['accuracy']:.3f}`",
            f"- Eval positive precision/recall/F1: `{eval_metrics['positive_precision']:.3f}` / `{eval_metrics['positive_recall']:.3f}` / `{eval_metrics['positive_f1']:.3f}`",
            f"- Input-field violations: `{summary['input_field_violations']}`",
            f"- Eval target counts: `{_format_counts(summary.get('eval_target_counts', {}))}`",
            "",
            "## Learned Weights",
            "",
            "| Feature | Weight |",
            "| --- | ---: |",
            *_format_weights(summary["model"]),
            "",
            "## Interpretation",
            "",
            "R168 provides the fallback boundary that R167 needs before broad API evaluation. "
            "The selector is trained only on label-free graph/objective features and R166 "
            "positive/fallback targets. It should be used as a deployment gate, not as an "
            "answer selector.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train R168 selector over R166 PromptEdge targets.")
    parser.add_argument(
        "--input-jsonl",
        default="experiment/aqua/aqua_first200_r166_expanded_selective_promptedge_rows.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_r168_promptedge_selector_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_r168_promptedge_selector_report.md",
    )
    parser.add_argument("--train-slice", default="aqua_100")
    parser.add_argument("--eval-slice", default="aqua_next100")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_jsonl_rows(args.input_jsonl)
    summary = build_selector_summary(
        rows,
        train_slice=args.train_slice,
        eval_slice=args.eval_slice,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
    )
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary))
    print(
        "R168 selector: "
        f"train_rows={summary['train_rows']} eval_rows={summary['eval_rows']} "
        f"eval_agreement={summary['eval_metrics']['accuracy']:.3f} "
        f"positive_recall={summary['eval_metrics']['positive_recall']:.3f} "
        f"input_violations={summary['input_field_violations']}"
    )


if __name__ == "__main__":
    main()
