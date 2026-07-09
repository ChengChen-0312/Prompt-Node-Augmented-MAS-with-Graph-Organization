import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.clean_fix_selector_ranker import (  # noqa: E402
    FORBIDDEN_INPUT_FIELDS,
    predict_label,
    predict_score,
)
from experiment.aqua.contract_graph_objective import (  # noqa: E402
    is_solved,
    ratio_text,
    summarize_selector_records,
)
from experiment.aqua.graph_policy_distill_export import normalize_graph_for_policy  # noqa: E402
from experiment.aqua.offline_utility_selector import normalize_option  # noqa: E402


RULE_NAME = "r079_r078_selector_tail34_replay"
FLOAT_TOLERANCE = 1e-12


def load_json(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_objective_records(path: str) -> List[Dict[str, Any]]:
    payload = load_json(path)
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError(f"No records list found in {path}")
    return records


def load_r078_model(path: str) -> Dict[str, Any]:
    payload = load_json(path)
    model = payload.get("model")
    if not isinstance(model, dict):
        raise ValueError(f"No R078 model found in {path}")
    return model


def _top_stats(variants: Sequence[Dict[str, Any]]) -> Tuple[float, int, float]:
    scores = sorted([float(variant.get("score") or 0.0) for variant in variants], reverse=True)
    if not scores:
        return 0.0, 0, 0.0
    top_score = scores[0]
    top_tie = sum(1 for score in scores if abs(score - top_score) <= FLOAT_TOLERANCE)
    lower_scores = [score for score in scores if score < top_score - FLOAT_TOLERANCE]
    margin = top_score - max(lower_scores) if lower_scores else 0.0
    return top_score, top_tie, margin


def _objective_bucket(variant: Dict[str, Any], top_score: float, top_tie: int, margin: float) -> str:
    score = float(variant.get("score") or 0.0)
    if abs(score - top_score) > FLOAT_TOLERANCE:
        return "non_preferred_graph"
    if top_tie > 1:
        return "multi_view_tie"
    if margin < 3:
        return "low_margin_top"
    return "preferred_graph"


def _graph_observation(variant: Dict[str, Any]) -> Dict[str, Any]:
    generated_graph = variant.get("generated_graph")
    if isinstance(generated_graph, dict):
        policy_graph = normalize_graph_for_policy(generated_graph)
        return {
            "num_prompt_nodes": policy_graph["num_prompt_nodes"],
            "num_prompt_node_edges": policy_graph["num_prompt_node_edges"],
            "prompt_node_role_counts": policy_graph["prompt_node_role_counts"],
            "prompt_node_edge_role_pairs": policy_graph["prompt_node_edge_role_pairs"],
            "has_promptnode_specs": bool(policy_graph["prompt_node_specs"]),
            "has_promptnode_edge_permissions": bool(policy_graph["prompt_node_edge_permissions"]),
        }
    return {
        "num_prompt_nodes": 0,
        "num_prompt_node_edges": 0,
        "prompt_node_role_counts": {},
        "prompt_node_edge_role_pairs": [],
        "has_promptnode_specs": False,
        "has_promptnode_edge_permissions": False,
    }


def variant_to_selector_row(
    record: Dict[str, Any],
    variant: Dict[str, Any],
    top_score: float,
    top_tie: int,
    margin: float,
) -> Dict[str, Any]:
    bucket = _objective_bucket(variant, top_score, top_tie, margin)
    score_is_top = abs(float(variant.get("score") or 0.0) - top_score) <= FLOAT_TOLERANCE
    return {
        "selector_policy_input": {
            "slice_prefix": record.get("slice_prefix"),
            "question": "",
            "candidate_method": variant.get("method_key"),
            "label_free_objective_features": {
                "objective_bucket": bucket,
                "objective_bucket_flags": {
                    "preferred_graph": bucket == "preferred_graph",
                    "multi_view_tie": bucket == "multi_view_tie",
                    "low_margin_top": bucket == "low_margin_top",
                    "non_positive_top": bucket == "non_positive_top",
                    "non_preferred_graph": bucket == "non_preferred_graph",
                },
                "objective_reward": variant.get("score"),
                "score_margin_to_next": margin if score_is_top and top_tie == 1 else None,
                "has_margin_at_least_3": bool(score_is_top and top_tie == 1 and margin >= 3),
                "score_components": variant.get("score_components") or {},
            },
            "candidate_graph_observation": _graph_observation(variant),
        },
        "clean_fix_distillation_target": {"target_class": "unknown_tail34_replay"},
    }


def _field_violates(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_INPUT_FIELDS:
                return True
            if _field_violates(child):
                return True
    elif isinstance(value, list):
        return any(_field_violates(child) for child in value)
    return False


def select_record_prediction(record: Dict[str, Any], model: Dict[str, Any]) -> Dict[str, Any]:
    variants = list(record.get("ranked_variants") or [])
    top_score, top_tie, margin = _top_stats(variants)
    scored_variants = []
    for variant in variants:
        selector_row = variant_to_selector_row(record, variant, top_score, top_tie, margin)
        score = predict_score(model, selector_row)
        positive = bool(predict_label(model, selector_row))
        option = normalize_option(variant.get("router_option")) or normalize_option(variant.get("predicted_answer"))
        scored_variants.append(
            {
                "method_key": variant.get("method_key"),
                "method_index": int(variant.get("method_index", 999) or 999),
                "selector_score": score,
                "selector_positive": positive,
                "selection_option": option,
                "objective_score": variant.get("score"),
                "objective_bucket": (selector_row["selector_policy_input"]["label_free_objective_features"]["objective_bucket"]),
                "candidate_graph_observation": selector_row["selector_policy_input"]["candidate_graph_observation"],
                "selector_input_violation": _field_violates(selector_row["selector_policy_input"]),
            }
        )
    scored_variants.sort(
        key=lambda item: (
            -float(item["selector_score"]),
            int(item.get("method_index", 999)),
            str(item.get("method_key")),
        )
    )
    baseline_prediction = normalize_option(record.get("baseline_prediction"))
    selected_prediction = baseline_prediction
    selected_source = "baseline"
    selected_method = None
    selector_positive = False
    positive_variants = [
        variant
        for variant in scored_variants
        if variant["selector_positive"] and float(variant["selector_score"]) > 0
    ]
    if positive_variants:
        best_score = float(positive_variants[0]["selector_score"])
        top_positive = [
            variant
            for variant in positive_variants
            if abs(float(variant["selector_score"]) - best_score) <= FLOAT_TOLERANCE
        ]
        top_options = {variant.get("selection_option") for variant in top_positive}
        top_options.discard(None)
        if len(top_options) == 1:
            selected_prediction = next(iter(top_options))
            if selected_prediction != baseline_prediction:
                selected_source = "r078_clean_fix_selector"
                selected_method = positive_variants[0].get("method_key")
                selector_positive = True

    true_answer = record.get("true_answer")
    return {
        "task_id": record.get("task_id"),
        "slice_prefix": record.get("slice_prefix"),
        "true_answer": true_answer,
        "baseline_prediction": baseline_prediction,
        "baseline_is_solved": is_solved(baseline_prediction, true_answer),
        "predicted_answer": selected_prediction,
        "is_solved": is_solved(selected_prediction, true_answer),
        "selected_source": selected_source,
        "selected_method": selected_method,
        "selector_positive": selector_positive,
        "top_objective_score": top_score,
        "top_objective_tie_count": top_tie,
        "top_objective_margin": margin,
        "selector_top_score": scored_variants[0]["selector_score"] if scored_variants else 0.0,
        "selector_scored_variants": scored_variants,
    }


def _variant_metadata_counts(records: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    total = with_generated_graph = with_promptnode_graph = with_promptnode_specs = 0
    for record in records:
        for variant in record.get("ranked_variants") or []:
            total += 1
            if isinstance(variant.get("generated_graph"), dict):
                with_generated_graph += 1
                graph_obs = _graph_observation(variant)
                if graph_obs["num_prompt_nodes"] > 0:
                    with_promptnode_graph += 1
                if graph_obs["has_promptnode_specs"]:
                    with_promptnode_specs += 1
    return {
        "total_variants": total,
        "variants_with_generated_graph": with_generated_graph,
        "variants_with_explicit_promptnode_graph": with_promptnode_graph,
        "variants_with_promptnode_specs": with_promptnode_specs,
    }


def _selector_feature_violations(records: Sequence[Dict[str, Any]]) -> int:
    violations = 0
    for record in records:
        for variant in record.get("selector_scored_variants") or []:
            if variant.get("selector_input_violation"):
                violations += 1
    return violations


def build_tail34_replay_payload(
    objective_summary_json: str = "experiment/aqua/res_logs/aqua_tail34_contract_graph_objective_summary.json",
    model_summary_json: str = "experiment/aqua/res_logs/aqua_first200_r078_clean_fix_selector_summary.json",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    objective_records = load_objective_records(objective_summary_json)
    model = load_r078_model(model_summary_json)
    records = [select_record_prediction(record, model) for record in objective_records]
    metadata_counts = _variant_metadata_counts(objective_records)
    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "objective_summary_json": objective_summary_json,
        "model_summary_json": model_summary_json,
        "total_tasks": len(records),
        "overall": summarize_selector_records(records),
        "selector_feature_violations": _selector_feature_violations(records),
        **metadata_counts,
        "claim_boundary": (
            "R079 is a replay applying the R078 selector to existing tail34 graph-objective traces. It exposes the "
            "missing explicit PromptNode graph metadata boundary: current tail34 traces contain no generated graph specs, "
            "so the selector falls back to baseline and does not create a new answer-accuracy gain."
        ),
    }
    return records, summary


def write_json(path: str, payload: Dict[str, Any]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def render_report(summary: Dict[str, Any], output_jsonl: str) -> str:
    overall = summary["overall"]
    return "\n".join(
        [
            "# R079 R078 Selector Tail34 Replay",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Output records: `{output_jsonl}`",
            f"- Overall selector accuracy: `{overall['overall']}`",
            f"- Baseline accuracy: `{overall['baseline']}`",
            f"- Delta vs baseline: `{overall['delta_vs_baseline']:+d}`",
            f"- Switches: `{overall['switches']}`",
            f"- Fix/Harm: `{overall['fix_harm']}`",
            f"- Selector feature violations: `{summary['selector_feature_violations']}`",
            f"- Total variants: `{summary['total_variants']}`",
            f"- Variants with generated graph: `{summary['variants_with_generated_graph']}`",
            f"- Variants with explicit PromptNode graph: `{summary['variants_with_explicit_promptnode_graph']}`",
            f"- Variants with PromptNode specs: `{summary['variants_with_promptnode_specs']}`",
            "",
            "## Interpretation",
            "",
            "The R078 selector is learnable on R077 rows, but this tail34 replay shows it cannot be expected to recover "
            "the R065/R068 accuracy signal unless the evaluated traces expose the same first-class PromptNode graph "
            "metadata used during training. This strengthens the next-step requirement: generate/evaluate PromptNode "
            "graphs before execution, then apply the selector to those graph candidates.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay the R078 selector over tail34 objective traces.")
    parser.add_argument(
        "--objective-summary-json",
        default="experiment/aqua/res_logs/aqua_tail34_contract_graph_objective_summary.json",
    )
    parser.add_argument(
        "--model-summary-json",
        default="experiment/aqua/res_logs/aqua_first200_r078_clean_fix_selector_summary.json",
    )
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_tail34_r079_clean_fix_selector_replay_results.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_tail34_r079_clean_fix_selector_replay_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_tail34_r079_clean_fix_selector_replay_report.md",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    records, summary = build_tail34_replay_payload(
        objective_summary_json=args.objective_summary_json,
        model_summary_json=args.model_summary_json,
    )
    write_jsonl(args.output_jsonl, records)
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary, args.output_jsonl))
    overall = summary["overall"]
    print(
        "Replayed R078 selector on tail34: "
        f"accuracy={overall['overall']} baseline={overall['baseline']} "
        f"switches={overall['switches']} promptnode_specs={summary['variants_with_promptnode_specs']}"
    )


if __name__ == "__main__":
    main()
