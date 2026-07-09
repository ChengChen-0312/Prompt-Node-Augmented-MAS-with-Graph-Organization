import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.contract_graph_objective import (  # noqa: E402
    is_solved,
    ratio_text,
    summarize_selector_records,
)
from experiment.aqua.graph_preference_ranker import FEATURE_NAMES  # noqa: E402
from experiment.aqua.offline_utility_selector import normalize_option  # noqa: E402


COMPONENT_FEATURES = {
    "strong_contract",
    "direct_agreement",
    "direct_vote_support",
    "prompt_node_graph",
    "conflict_penalty",
    "weak_contract_penalty",
}

DISALLOWED_SELECTOR_FIELDS = {
    "objective_score",
    "predicted_answer",
    "router_option",
    "true_answer",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
}

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


def load_ranker_model(path: str) -> Dict[str, Any]:
    payload = load_json(path)
    model = payload.get("model", payload)
    if "weights" not in model:
        raise ValueError(f"No ranker weights found in {path}")
    return model


def selector_features(variant: Dict[str, Any]) -> Dict[str, float]:
    components = variant.get("score_components") or {}
    features: Dict[str, float] = {}
    for name in FEATURE_NAMES:
        if name in COMPONENT_FEATURES:
            features[name] = float(components.get(name, 0) or 0)
        elif name == "strong_router_contract_count":
            features[name] = float(variant.get("strong_router_contract_count", 0) or 0)
        elif name in {"router_matches_direct_majority", "has_prompt_node_graph"}:
            features[name] = 1.0 if variant.get(name) else 0.0
        else:
            features[name] = 0.0
    return features


def score_variant(model: Dict[str, Any], variant: Dict[str, Any]) -> float:
    weights = model.get("weights", {})
    features = selector_features(variant)
    return sum(float(weights.get(name, 0.0)) * features[name] for name in FEATURE_NAMES)


def _ranker_scored_variants(
    ranked_variants: Sequence[Dict[str, Any]],
    model: Dict[str, Any],
) -> List[Dict[str, Any]]:
    scored = []
    for variant in ranked_variants:
        features = selector_features(variant)
        scored.append(
            {
                "method_key": variant.get("method_key"),
                "method_index": int(variant.get("method_index", 999) or 999),
                "ranker_score": score_variant(model, variant),
                "selector_features": features,
                "selection_option": normalize_option(variant.get("router_option"))
                or normalize_option(variant.get("predicted_answer")),
            }
        )
    return sorted(
        scored,
        key=lambda item: (
            -float(item["ranker_score"]),
            int(item.get("method_index", 999)),
            str(item.get("method_key")),
        ),
    )


def _top_margin(scored_variants: Sequence[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]], float]:
    if not scored_variants:
        return 0.0, [], 0.0
    top_score = float(scored_variants[0]["ranker_score"])
    top_variants = [
        variant
        for variant in scored_variants
        if abs(float(variant["ranker_score"]) - top_score) <= FLOAT_TOLERANCE
    ]
    if len(top_variants) > 1:
        return top_score, top_variants, 0.0
    lower_scores = [
        float(variant["ranker_score"])
        for variant in scored_variants
        if float(variant["ranker_score"]) < top_score - FLOAT_TOLERANCE
    ]
    margin = top_score - max(lower_scores) if lower_scores else 0.0
    return top_score, top_variants, margin


def select_ranker_guided_prediction(
    baseline_prediction: Any,
    ranked_variants: Sequence[Dict[str, Any]],
    model: Dict[str, Any],
    min_ranker_score: float = 0.1,
    min_ranker_margin: float = 0.1,
) -> Tuple[Optional[str], str, Optional[str], float, float]:
    baseline_option = normalize_option(baseline_prediction)
    scored_variants = _ranker_scored_variants(ranked_variants, model)
    top_score, top_variants, margin = _top_margin(scored_variants)
    if not top_variants:
        return baseline_option, "baseline", None, top_score, margin
    if top_score < min_ranker_score or margin < min_ranker_margin:
        return baseline_option, "baseline", None, top_score, margin

    top_options = {variant.get("selection_option") for variant in top_variants}
    top_options.discard(None)
    if len(top_options) != 1:
        return baseline_option, "baseline", None, top_score, margin

    selected = next(iter(top_options))
    top_method = str(top_variants[0].get("method_key"))
    if selected == baseline_option:
        return baseline_option, "baseline", top_method, top_score, margin
    return selected, "ranker_top", top_method, top_score, margin


def build_ranker_selector_records(
    objective_records: Sequence[Dict[str, Any]],
    model: Dict[str, Any],
    min_ranker_score: float = 0.1,
    min_ranker_margin: float = 0.1,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for record in objective_records:
        ranked_variants = list(record.get("ranked_variants") or [])
        baseline_prediction = normalize_option(record.get("baseline_prediction"))
        selected_prediction, selected_source, selected_method, top_score, margin = select_ranker_guided_prediction(
            baseline_prediction,
            ranked_variants,
            model,
            min_ranker_score=min_ranker_score,
            min_ranker_margin=min_ranker_margin,
        )
        scored_variants = _ranker_scored_variants(ranked_variants, model)
        top_features = scored_variants[0]["selector_features"] if scored_variants else {}
        true_answer = record.get("true_answer")
        records.append(
            {
                "task_id": record.get("task_id"),
                "slice_prefix": record.get("slice_prefix"),
                "true_answer": true_answer,
                "predicted_answer": selected_prediction,
                "is_solved": is_solved(selected_prediction, true_answer),
                "selected_source": selected_source,
                "selected_method": selected_method,
                "baseline_prediction": baseline_prediction,
                "baseline_is_solved": is_solved(baseline_prediction, true_answer),
                "selector_rule": "pairwise_graph_ranker_unique_top",
                "min_ranker_score": min_ranker_score,
                "min_ranker_margin": min_ranker_margin,
                "ranker_top_score": top_score,
                "ranker_score_margin": margin,
                "ranker_top_method": scored_variants[0].get("method_key") if scored_variants else None,
                "selector_features": top_features,
                "ranker_scored_variants": scored_variants,
            }
        )
    return records


def _selector_feature_violations(records: Sequence[Dict[str, Any]]) -> int:
    violations = 0
    for record in records:
        if DISALLOWED_SELECTOR_FIELDS.intersection(record.get("selector_features", {})):
            violations += 1
            continue
        for variant in record.get("ranker_scored_variants", []):
            if DISALLOWED_SELECTOR_FIELDS.intersection(variant.get("selector_features", {})):
                violations += 1
                break
    return violations


def summarize_ranker_selector_records(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    records_list = list(records)
    by_slice: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records_list:
        by_slice[str(record.get("slice_prefix"))].append(record)

    return {
        "feature_names": FEATURE_NAMES,
        "excluded_selector_fields": sorted(DISALLOWED_SELECTOR_FIELDS),
        "outcome_field_violations": _selector_feature_violations(records_list),
        "overall": summarize_selector_records(records_list),
        "slice_summaries": {
            slice_prefix: summarize_selector_records(slice_records)
            for slice_prefix, slice_records in sorted(by_slice.items())
        },
        "claim_boundary": (
            "Ranker-guided selector replay over existing first200 traces. The selection features exclude gold answers, "
            "audit labels, correctness fields, predicted options, router options, and objective_score. true_answer is "
            "used only after selection for post-hoc answer-accuracy accounting."
        ),
    }


def render_report(summary: Dict[str, Any], output_jsonl: str) -> str:
    overall = summary["overall"]
    slice_lines = []
    for slice_prefix, slice_summary in summary.get("slice_summaries", {}).items():
        slice_lines.append(
            f"| `{slice_prefix}` | `{slice_summary['overall']}` | `{slice_summary['baseline']}` | "
            f"`{slice_summary['delta_vs_baseline']:+d}` | `{slice_summary['fix_harm']}` | "
            f"`{slice_summary['switches']}` |"
        )

    return "\n".join(
        [
            "# AQuA First200 Graph-Ranker-Guided Selector Replay",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Selector records: `{output_jsonl}`",
            f"- Overall selector accuracy: `{overall['overall']}`",
            f"- ARG baseline accuracy: `{overall['baseline']}`",
            f"- Delta vs ARG: `{overall['delta_vs_baseline']:+d}`",
            f"- Fix/Harm vs ARG: `{overall['fix_harm']}`",
            f"- Switches: `{overall['switches']}`",
            f"- Outcome-field violations in selector features: `{summary['outcome_field_violations']}`",
            "",
            "## Slice Summary",
            "",
            "| Slice | Selector | ARG baseline | Delta | Fix/Harm | Switches |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            *slice_lines,
            "",
            "## Interpretation",
            "",
            "This replay turns the R050 pairwise graph preference ranker into a prospective selector over already generated "
            "PromptNode graph variants. It is closer to the user's intended virtual-node setup than answer-level patching "
            "because the learned score ranks graph organizations before final answer aggregation.",
            "",
            "The result is still an offline replay on first200 traces, not a new same-model API validation. It should be used "
            "as an ablation and bridge toward training-time graph selection; tail34 and transfer validation remain blocked "
            "until the same-model quota issue is resolved.",
            "",
        ]
    )


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay a label-free pairwise graph-ranker as a PromptNode graph selector."
    )
    parser.add_argument(
        "--objective-summary-json",
        default="experiment/aqua/res_logs/aqua_first200_contract_graph_objective_summary.json",
    )
    parser.add_argument(
        "--ranker-summary-json",
        default="experiment/aqua/res_logs/aqua_first200_graph_preference_ranker_summary.json",
    )
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_first200_graph_ranker_selector_results.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_graph_ranker_selector_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_graph_ranker_selector_report.md",
    )
    parser.add_argument("--min-ranker-score", type=float, default=0.1)
    parser.add_argument("--min-ranker-margin", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    objective_records = load_objective_records(args.objective_summary_json)
    model = load_ranker_model(args.ranker_summary_json)
    records = build_ranker_selector_records(
        objective_records,
        model,
        min_ranker_score=args.min_ranker_score,
        min_ranker_margin=args.min_ranker_margin,
    )
    summary = summarize_ranker_selector_records(records)
    payload = {
        "objective_summary_json": args.objective_summary_json,
        "ranker_summary_json": args.ranker_summary_json,
        "output_jsonl": args.output_jsonl,
        "min_ranker_score": args.min_ranker_score,
        "min_ranker_margin": args.min_ranker_margin,
        **summary,
    }
    write_jsonl(args.output_jsonl, records)
    write_json(args.summary_json, payload)
    write_text(args.report_md, render_report(payload, args.output_jsonl))
    print(
        "Replayed graph-ranker selector: "
        f"overall={summary['overall']['overall']} baseline={summary['overall']['baseline']} "
        f"delta={summary['overall']['delta_vs_baseline']:+d} "
        f"fix_harm={summary['overall']['fix_harm']} "
        f"switches={summary['overall']['switches']}"
    )


if __name__ == "__main__":
    main()
