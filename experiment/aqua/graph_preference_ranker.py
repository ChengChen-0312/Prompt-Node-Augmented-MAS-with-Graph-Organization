import argparse
import json
import os
import sys
from typing import Any, Dict, List, Sequence

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402


COMPONENT_FEATURES = [
    "strong_contract",
    "direct_agreement",
    "direct_vote_support",
    "prompt_node_graph",
    "conflict_penalty",
    "weak_contract_penalty",
]

EXTRA_FEATURES = [
    "strong_router_contract_count",
    "router_matches_direct_majority",
    "has_prompt_node_graph",
]

FEATURE_NAMES = COMPONENT_FEATURES + EXTRA_FEATURES

DISALLOWED_OUTCOME_FIELDS = {
    "true_answer",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "r035_selected_prediction",
    "r035_selected_source",
}


def _view_feature(view: Dict[str, Any], name: str) -> float:
    if name in COMPONENT_FEATURES:
        return float((view.get("score_components") or {}).get(name, 0) or 0)
    if name == "strong_router_contract_count":
        return float(view.get("strong_router_contract_count", 0) or 0)
    if name in {"router_matches_direct_majority", "has_prompt_node_graph"}:
        return 1.0 if view.get(name) else 0.0
    return 0.0


def pair_feature_diff(pair: Dict[str, Any]) -> List[float]:
    positive = pair.get("positive", {})
    negative = pair.get("negative", {})
    return [_view_feature(positive, name) - _view_feature(negative, name) for name in FEATURE_NAMES]


def dot(weights: Sequence[float], features: Sequence[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, features))


def train_pairwise_ranker(
    pairs: Sequence[Dict[str, Any]],
    epochs: int = 20,
    learning_rate: float = 0.1,
) -> Dict[str, Any]:
    weights = [0.0 for _ in FEATURE_NAMES]
    updates = 0
    for _ in range(epochs):
        for pair in pairs:
            features = pair_feature_diff(pair)
            if dot(weights, features) <= 0:
                weights = [weight + learning_rate * value for weight, value in zip(weights, features)]
                updates += 1
    return {
        "feature_names": FEATURE_NAMES,
        "weights": {name: weights[index] for index, name in enumerate(FEATURE_NAMES)},
        "epochs": epochs,
        "learning_rate": learning_rate,
        "updates": updates,
        "claim_boundary": (
            "Pairwise graph-ranker trained on label-free graph-objective preferences. "
            "The model does not use gold answers, audit labels, correctness fields, predicted options, or objective_score."
        ),
    }


def _weight_vector(model: Dict[str, Any]) -> List[float]:
    weights = model.get("weights", {})
    return [float(weights.get(name, 0.0)) for name in FEATURE_NAMES]


def evaluate_ranker(model: Dict[str, Any], pairs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    weights = _weight_vector(model)
    margins = [dot(weights, pair_feature_diff(pair)) for pair in pairs]
    correct = sum(1 for margin in margins if margin > 0)
    total = len(margins)
    return {
        "total_pairs": total,
        "correct_pairs": correct,
        "accuracy": correct / total if total else 0.0,
        "mean_margin": sum(margins) / total if total else 0.0,
        "min_margin": min(margins) if margins else 0.0,
    }


def split_pairs_by_slice(
    pairs: Sequence[Dict[str, Any]],
    train_slice: str = "aqua_100",
    eval_slice: str = "aqua_next100",
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    train_pairs = [pair for pair in pairs if pair.get("slice_prefix") == train_slice]
    eval_pairs = [pair for pair in pairs if pair.get("slice_prefix") == eval_slice]
    return train_pairs, eval_pairs


def outcome_field_violations(pairs: Sequence[Dict[str, Any]]) -> int:
    violations = 0
    for pair in pairs:
        if DISALLOWED_OUTCOME_FIELDS.intersection(pair):
            violations += 1
            continue
        if DISALLOWED_OUTCOME_FIELDS.intersection(pair.get("positive", {})):
            violations += 1
            continue
        if DISALLOWED_OUTCOME_FIELDS.intersection(pair.get("negative", {})):
            violations += 1
    return violations


def build_ranker_summary(
    pairs: Sequence[Dict[str, Any]],
    train_slice: str = "aqua_100",
    eval_slice: str = "aqua_next100",
    epochs: int = 20,
    learning_rate: float = 0.1,
) -> Dict[str, Any]:
    train_pairs, eval_pairs = split_pairs_by_slice(pairs, train_slice=train_slice, eval_slice=eval_slice)
    model = train_pairwise_ranker(train_pairs, epochs=epochs, learning_rate=learning_rate)
    train_metrics = evaluate_ranker(model, train_pairs)
    eval_metrics = evaluate_ranker(model, eval_pairs)
    return {
        "train_slice": train_slice,
        "eval_slice": eval_slice,
        "source_pairs": len(pairs),
        "train_pairs": len(train_pairs),
        "eval_pairs": len(eval_pairs),
        "feature_names": FEATURE_NAMES,
        "model": model,
        "train_accuracy": train_metrics["accuracy"],
        "eval_accuracy": eval_metrics["accuracy"],
        "train_metrics": train_metrics,
        "eval_metrics": eval_metrics,
        "outcome_field_violations": outcome_field_violations(pairs),
        "excluded_outcome_fields": sorted(DISALLOWED_OUTCOME_FIELDS),
        "excluded_feature_fields": [
            "objective_score",
            "predicted_answer",
            "router_option",
            "true_answer",
            "audit_label",
            "is_solved",
        ],
        "claim_boundary": (
            "Offline graph-ranker fit to label-free PromptNode graph-objective pairwise preferences. "
            "Accuracy here is preference agreement with the objective, not task-answer accuracy."
        ),
    }


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def render_report(summary: Dict[str, Any]) -> str:
    weights = summary["model"]["weights"]
    weight_lines = [f"| `{name}` | `{weights.get(name, 0.0):.4f}` |" for name in FEATURE_NAMES]
    return "\n".join(
        [
            "# AQuA First200 Pairwise Graph Preference Ranker",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Source pairs: `{summary['source_pairs']}`",
            f"- Train slice: `{summary['train_slice']}` with `{summary['train_pairs']}` pairs",
            f"- Eval slice: `{summary['eval_slice']}` with `{summary['eval_pairs']}` pairs",
            f"- Train preference agreement: `{summary['train_accuracy']:.3f}`",
            f"- Eval preference agreement: `{summary['eval_accuracy']:.3f}`",
            f"- Outcome-field violations: `{summary['outcome_field_violations']}`",
            "",
            "## Learned Feature Weights",
            "",
            "| Feature | Weight |",
            "| --- | ---: |",
            *weight_lines,
            "",
            "## Interpretation",
            "",
            "This ranker is a proof-of-interface for training PromptNode graph selection before final answer aggregation. "
            "It learns from pairwise graph preferences derived from contract evidence, not from gold answers or clean/noisy labels. "
            "The reported agreement is only agreement with the label-free graph objective; it is not AQuA answer accuracy.",
            "",
        ]
    )


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train an offline pairwise ranker over label-free PromptNode graph preferences."
    )
    parser.add_argument(
        "--input-jsonl",
        default="experiment/aqua/aqua_first200_graph_objective_pairwise_preferences.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_graph_preference_ranker_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_graph_preference_ranker_report.md",
    )
    parser.add_argument("--train-slice", default="aqua_100")
    parser.add_argument("--eval-slice", default="aqua_next100")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pairs = load_jsonl_rows(args.input_jsonl)
    summary = build_ranker_summary(
        pairs,
        train_slice=args.train_slice,
        eval_slice=args.eval_slice,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
    )
    summary["input_jsonl"] = args.input_jsonl
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary))
    print(
        "Trained graph preference ranker: "
        f"train_pairs={summary['train_pairs']} eval_pairs={summary['eval_pairs']} "
        f"eval_agreement={summary['eval_accuracy']:.3f}"
    )


if __name__ == "__main__":
    main()
