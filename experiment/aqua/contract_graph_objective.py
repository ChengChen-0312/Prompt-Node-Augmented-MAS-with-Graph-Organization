import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.offline_utility_selector import (  # noqa: E402
    DEFAULT_CONTRACT_METHOD_KEYS,
    common_task_ids,
    extract_contract_consensus_features,
    graph_has_prompt_node,
    load_prefix_result_sets,
    normalize_option,
)


def score_contract_features(
    features: Dict[str, Any],
    has_prompt_node_graph: bool = False,
) -> Dict[str, Any]:
    components = {
        "strong_contract": 0,
        "direct_agreement": 0,
        "direct_vote_support": 0,
        "prompt_node_graph": 0,
        "conflict_penalty": 0,
        "weak_contract_penalty": 0,
    }
    if normalize_option(features.get("router_option")) and features.get(
        "strong_router_contract_count", 0
    ) > 0:
        components["strong_contract"] = 4
    if features.get("router_matches_direct_majority"):
        components["direct_agreement"] = 3
    components["direct_vote_support"] = min(int(features.get("direct_majority_count", 0) or 0), 3)
    if has_prompt_node_graph:
        components["prompt_node_graph"] = 1
    if features.get("router_conflicts_with_direct_majority"):
        components["conflict_penalty"] = -4
    if features.get("all_router_contracts_weak"):
        components["weak_contract_penalty"] = -2
    return {
        "score": sum(components.values()),
        "components": components,
    }


def rank_task_variants(
    task_id: str,
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    method_keys: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    method_keys = method_keys or DEFAULT_CONTRACT_METHOD_KEYS
    ranked = []
    for index, method_key in enumerate(method_keys):
        record = result_sets.get(method_key, {}).get(task_id)
        if not record:
            continue
        features = extract_contract_consensus_features(record)
        has_prompt_node_graph = graph_has_prompt_node(record.get("generated_graph"))
        score = score_contract_features(features, has_prompt_node_graph=has_prompt_node_graph)
        ranked.append(
            {
                "method_key": method_key,
                "method_index": index,
                "score": score["score"],
                "score_components": score["components"],
                "router_option": features.get("router_option"),
                "direct_majority": features.get("direct_majority"),
                "router_matches_direct_majority": features.get("router_matches_direct_majority"),
                "strong_router_contract_count": features.get("strong_router_contract_count", 0),
                "has_prompt_node_graph": has_prompt_node_graph,
                "predicted_answer": normalize_option(record.get("predicted_answer")),
            }
        )
    return sorted(ranked, key=lambda item: (-item["score"], item["method_index"], item["method_key"]))


def is_solved(prediction: Any, true_answer: Any) -> bool:
    return normalize_option(prediction) == normalize_option(true_answer)


def ratio_text(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}"


def build_objective_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    top_methods: Counter[str] = Counter()
    top_score_ties = 0
    positive_top_score_tasks = 0
    top_scores = []
    diagnostic_answer_total = 0
    diagnostic_answer_solved = 0
    r035_pure_switch_tasks = 0
    r035_switch_top_option_agreement = 0
    r035_switch_unique_top_option_agreement = 0

    for record in records:
        ranked = record.get("ranked_variants") or []
        if not ranked:
            continue
        top_score = ranked[0]["score"]
        top_scores.append(top_score)
        if top_score > 0:
            positive_top_score_tasks += 1
        tied_top = [item for item in ranked if item["score"] == top_score]
        if len(tied_top) > 1:
            top_score_ties += 1
        else:
            top_methods[ranked[0]["method_key"]] += 1
        if record.get("top_prediction") is not None and record.get("true_answer") is not None:
            diagnostic_answer_total += 1
            diagnostic_answer_solved += int(is_solved(record["top_prediction"], record["true_answer"]))
        if record.get("r035_selected_source") == "multi_contract_union":
            r035_pure_switch_tasks += 1
            selected_option = normalize_option(record.get("r035_selected_prediction"))
            top_options = {
                normalize_option(item.get("router_option"))
                for item in ranked
                if item["score"] == top_score
            }
            if selected_option in top_options:
                r035_switch_top_option_agreement += 1
                if len(tied_top) == 1:
                    r035_switch_unique_top_option_agreement += 1

    total = len(records)
    mean_top_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
    return {
        "total_tasks": total,
        "positive_top_score_tasks": positive_top_score_tasks,
        "positive_top_score_rate": positive_top_score_tasks / total if total else 0.0,
        "mean_top_score": mean_top_score,
        "top_score_ties": top_score_ties,
        "unique_top_method_distribution": dict(sorted(top_methods.items())),
        "diagnostic_selected_method_answer_solved": diagnostic_answer_solved,
        "diagnostic_selected_method_answer_total": diagnostic_answer_total,
        "diagnostic_selected_method_answer_accuracy": (
            diagnostic_answer_solved / diagnostic_answer_total if diagnostic_answer_total else 0.0
        ),
        "r035_pure_switch_tasks": r035_pure_switch_tasks,
        "r035_switch_top_option_agreement": r035_switch_top_option_agreement,
        "r035_switch_unique_top_option_agreement": r035_switch_unique_top_option_agreement,
    }


def select_objective_guided_prediction(
    baseline_prediction: Any,
    ranked_variants: List[Dict[str, Any]],
    min_top_score: int = 1,
    min_score_margin: int = 0,
) -> tuple[Optional[str], str]:
    baseline_option = normalize_option(baseline_prediction)
    if not ranked_variants:
        return baseline_option, "baseline"
    top_score = ranked_variants[0]["score"]
    if top_score < min_top_score:
        return baseline_option, "baseline"
    lower_scores = [variant["score"] for variant in ranked_variants if variant["score"] < top_score]
    if lower_scores and top_score - max(lower_scores) < min_score_margin:
        return baseline_option, "baseline"
    top_variants = [variant for variant in ranked_variants if variant["score"] == top_score]
    top_options = {
        normalize_option(variant.get("router_option")) or normalize_option(variant.get("predicted_answer"))
        for variant in top_variants
    }
    top_options.discard(None)
    if len(top_options) != 1:
        return baseline_option, "baseline"
    selected = next(iter(top_options))
    if selected == baseline_option:
        return baseline_option, "baseline"
    return selected, "objective_top"


def build_objective_records(
    prefixes: List[str],
    base_dir: str,
    method_keys: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    records = []
    for prefix in prefixes:
        result_sets = load_prefix_result_sets(prefix, base_dir)
        r035_records = {
            record["task_id"]: record
            for record in build_r035_reference_records(result_sets, common_task_ids(result_sets))
        }
        for task_id in common_task_ids(result_sets):
            ranked = rank_task_variants(task_id, result_sets, method_keys=method_keys)
            baseline_record = result_sets["baseline"][task_id]
            top = ranked[0] if ranked else {}
            r035_record = r035_records.get(task_id, {})
            records.append(
                {
                    "task_id": task_id,
                    "slice_prefix": prefix,
                    "ranked_variants": ranked,
                    "top_method": top.get("method_key"),
                    "top_score": top.get("score"),
                    "top_prediction": top.get("predicted_answer"),
                    "baseline_prediction": normalize_option(baseline_record.get("predicted_answer")),
                    "true_answer": baseline_record.get("true_answer"),
                    "r035_selected_source": r035_record.get("selected_source"),
                    "r035_selected_prediction": r035_record.get("predicted_answer"),
                }
            )
    return records


def build_r035_reference_records(
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
    task_ids: Iterable[str],
) -> List[Dict[str, Any]]:
    from experiment.aqua.offline_utility_selector import build_multi_contract_union_records

    return build_multi_contract_union_records(
        result_sets,
        task_ids,
        min_direct_methods=2,
        min_strong_methods=3,
        use_invalid_fallback=False,
    )


def build_objective_selector_records(
    prefixes: List[str],
    base_dir: str,
    method_keys: Optional[List[str]] = None,
    min_top_score: int = 1,
    min_score_margin: int = 0,
) -> List[Dict[str, Any]]:
    records = []
    for prefix in prefixes:
        result_sets = load_prefix_result_sets(prefix, base_dir)
        for task_id in common_task_ids(result_sets):
            baseline_record = result_sets["baseline"][task_id]
            ranked = rank_task_variants(task_id, result_sets, method_keys=method_keys)
            baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
            selected_prediction, selected_source = select_objective_guided_prediction(
                baseline_prediction,
                ranked,
                min_top_score=min_top_score,
                min_score_margin=min_score_margin,
            )
            true_answer = baseline_record.get("true_answer")
            records.append(
                {
                    "task_id": task_id,
                    "slice_prefix": prefix,
                    "question": baseline_record.get("question"),
                    "true_answer": true_answer,
                    "predicted_answer": selected_prediction,
                    "is_solved": is_solved(selected_prediction, true_answer),
                    "selected_source": selected_source,
                    "baseline_prediction": baseline_prediction,
                    "baseline_is_solved": is_solved(baseline_prediction, true_answer),
                    "selector_rule": "objective_guided_unique_top_option",
                    "min_top_score": min_top_score,
                    "min_score_margin": min_score_margin,
                    "top_score": ranked[0]["score"] if ranked else None,
                    "ranked_variants": ranked,
                }
            )
    return records


def summarize_selector_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    solved_count = sum(1 for record in records if is_solved(record.get("predicted_answer"), record.get("true_answer")))
    baseline_count = sum(
        1 for record in records if is_solved(record.get("baseline_prediction"), record.get("true_answer"))
    )
    fixes = sum(
        1
        for record in records
        if not is_solved(record.get("baseline_prediction"), record.get("true_answer"))
        and is_solved(record.get("predicted_answer"), record.get("true_answer"))
    )
    harms = sum(
        1
        for record in records
        if is_solved(record.get("baseline_prediction"), record.get("true_answer"))
        and not is_solved(record.get("predicted_answer"), record.get("true_answer"))
    )
    switches = sum(1 for record in records if record.get("selected_source") != "baseline")
    source_counts = Counter(str(record.get("selected_source", "baseline")) for record in records)
    return {
        "total_tasks": total,
        "solved_tasks": solved_count,
        "baseline_solved_tasks": baseline_count,
        "overall": ratio_text(solved_count, total),
        "baseline": ratio_text(baseline_count, total),
        "delta_vs_baseline": solved_count - baseline_count,
        "fixes": fixes,
        "harms": harms,
        "fix_harm": f"{fixes}/{harms}",
        "switches": switches,
        "selected_source_counts": dict(sorted(source_counts.items())),
    }


def summarize_selector_records_with_audit(
    records: List[Dict[str, Any]],
    audit_labels: Dict[str, str],
) -> Dict[str, Any]:
    from experiment.aqua.contract_ablation_analysis import summarize_variant_records

    return summarize_variant_records("objective_guided_selector", records, audit_labels)


def default_audit_files(base_dir: str, prefixes: List[str]) -> List[str]:
    return [
        os.path.join(base_dir, f"{prefix}_option_binding_audit.jsonl")
        for prefix in prefixes
        if os.path.exists(os.path.join(base_dir, f"{prefix}_option_binding_audit.jsonl"))
    ]


def format_selector_report(
    summary: Dict[str, Any],
    audit_summary: Optional[Dict[str, Any]] = None,
    min_score_margin: int = 0,
) -> str:
    clean_lines = []
    if audit_summary:
        clean_lines = [
            f"| Clean split | `{audit_summary['clean']}` |",
            f"| Noisy/Ambiguous split | `{audit_summary['noisy_or_ambiguous']}` |",
            f"| Clean Fix/Harm | `{audit_summary['clean_fix_harm']}` |",
            f"| Noisy/Ambiguous Fix/Harm | `{audit_summary['noisy_fix_harm']}` |",
        ]
    clean_harm_count = audit_summary.get("clean_harms", 0) if audit_summary else None
    run_name = (
        "Margin-Gated Objective-Guided PromptNode Variant Selector"
        if min_score_margin > 0
        else "Objective-Guided PromptNode Variant Selector"
    )
    safety_interpretation = (
        "The margin gate removes observed harms in this replay, making it safer than the ungated R039 selector. "
        "It still has lower clean coverage than R035 pure multi-contract selection, so R035 remains the stronger mechanism claim."
        if clean_harm_count == 0 and min_score_margin > 0
        else "The objective-guided selector is less clean-safe than R035 pure multi-contract selection when it introduces clean harm. "
        "R035 remains the safer mechanism claim until a stricter prospective selector is validated."
    )
    next_margin = (
        "Validate the margin-gated selector prospectively on tail34 and compare it against R035 pure/full selectors."
        if min_score_margin > 0
        else "Evaluate a margin-gated selector and compare clean fix/harm."
    )
    return "\n".join(
        [
            f"# AQuA First200 {run_name}",
            "",
            "## Raw Summary",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Min score margin | `{min_score_margin}` |",
            f"| Objective-guided selector | `{summary['overall']}` |",
            f"| ARG baseline | `{summary['baseline']}` |",
            f"| Delta vs ARG | `{summary['delta_vs_baseline']:+d}` |",
            f"| Fix/Harm vs ARG | `{summary['fix_harm']}` |",
            f"| Switches | `{summary['switches']}` |",
            f"| Source counts | `{format_distribution(summary['selected_source_counts'])}` |",
            *clean_lines,
            "",
            "## Interpretation",
            "",
            "This is an exploratory replay of the R038 graph-quality objective as a conservative answer selector. "
            "The selector switches away from ARG only when the top objective score maps to a unique valid option; "
            "otherwise it keeps ARG's baseline prediction. The rule uses PromptNode contract evidence and direct-agent agreement, "
            "not gold labels or audit labels.",
            "",
            "This result is not yet a prospective validation because it reuses first200 traces that informed method design. "
            "It should be treated as a candidate for tail34 or transfer validation once same-model API quota returns.",
            "",
            "## Key Findings",
            "",
            "1. **Observation**: Objective-guided selection reaches "
            f"`{summary['overall']}` versus ARG `{summary['baseline']}`, with fix/harm `{summary['fix_harm']}`. "
            "**Interpretation**: The contract-coverage objective can recover additional answer signal from PromptNode variants. "
            "**Implication**: R038 can be promoted from a graph-quality diagnostic to a candidate graph-selection rule. "
            "**Next step**: Validate prospectively on tail34 before using this as a main accuracy claim.",
            "",
            "2. **Observation**: The clean split is "
            + (
                f"`{audit_summary['clean']}` with clean fix/harm `{audit_summary['clean_fix_harm']}`. "
                if audit_summary
                else "not available in this run. "
            )
            + f"**Interpretation**: {safety_interpretation}"
            " **Implication**: Treat this as a system-candidate ablation, not as the final SCI claim. "
            f"**Next step**: {next_margin}",
            "",
            "3. **Observation**: The selector switches only on unique top objective options. "
            "**Interpretation**: This reduces blind switching under R038 ties; the score margin adds an additional separation constraint when enabled. "
            "**Implication**: The next graph objective should optimize separation between top variants, not only raw contract score. "
            "**Next step**: Use the selected margin as a pre-registered tail34 setting rather than tuning on tail34.",
            "",
            "## Suggested Next Experiments",
            "",
            "- Tail34 prospective replay for R035 pure/full, R039 ungated, and R040 margin-gated selectors once quota returns.",
            "- Transfer multiple-choice math validation with the same objective-gated selector.",
            "",
        ]
    )


def format_distribution(distribution: Dict[str, int]) -> str:
    if not distribution:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in distribution.items())


def format_markdown_report(summary: Dict[str, Any]) -> str:
    accuracy = summary["diagnostic_selected_method_answer_accuracy"] * 100
    positive_rate = summary["positive_top_score_rate"] * 100
    return "\n".join(
        [
            "# AQuA First200 Contract-Coverage Graph Objective",
            "",
            "## Raw Summary",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Total tasks | `{summary['total_tasks']}` |",
            f"| Positive top-score tasks | `{summary['positive_top_score_tasks']}` (`{positive_rate:.1f}%`) |",
            f"| Mean top score | `{summary['mean_top_score']:.3f}` |",
            f"| Top-score ties | `{summary['top_score_ties']}` |",
            f"| Unique top method distribution | `{format_distribution(summary['unique_top_method_distribution'])}` |",
            f"| Diagnostic selected-method answer accuracy | `{summary['diagnostic_selected_method_answer_solved']}/{summary['diagnostic_selected_method_answer_total']}` (`{accuracy:.1f}%`) |",
            f"| R035 pure switch tasks | `{summary['r035_pure_switch_tasks']}` |",
            f"| R035 switch top-option agreement | `{summary['r035_switch_top_option_agreement']}/{summary['r035_pure_switch_tasks']}` |",
            f"| R035 switch unique-top agreement | `{summary['r035_switch_unique_top_option_agreement']}/{summary['r035_pure_switch_tasks']}` |",
            "",
            "## Interpretation",
            "",
            "This report evaluates a label-free graph-quality objective, not a new answer selector. "
            "The score uses PromptNode router contracts, direct-agent agreement, PromptNode graph presence, "
            "and conflict/weak-contract penalties. Gold labels and clean/noisy audit labels are not objective inputs.",
            "",
            "A high positive top score means at least one PromptNode graph variant produced reusable option-binding evidence. "
            "Top-score ties indicate that the objective cannot uniquely choose one variant and should either retain multiple views "
            "or ask a future graph generator to increase contract separation.",
            "",
            "## Next Step",
            "",
            "Use this objective as a training or candidate-selection reward: prefer generated PromptNode graphs that raise strong, "
            "directly supported router contracts while avoiding conflict penalties. Validate prospectively on tail34 or transfer data "
            "before making any accuracy claim.",
            "",
        ]
    )


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def write_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze label-free PromptNode contract graph objective.")
    parser.add_argument("--prefix", action="append", dest="prefixes", default=[])
    parser.add_argument("--base-dir", default=os.path.dirname(__file__))
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--selector-output-jsonl")
    parser.add_argument("--selector-summary-json")
    parser.add_argument("--selector-report-md")
    parser.add_argument("--audit-file", action="append", dest="audit_files", default=[])
    parser.add_argument("--min-top-score", type=int, default=1)
    parser.add_argument("--min-score-margin", type=int, default=0)
    args = parser.parse_args()

    prefixes = args.prefixes or ["aqua_100", "aqua_next100"]
    records = build_objective_records(prefixes, args.base_dir)
    summary = build_objective_summary(records)
    payload = {
        "prefixes": prefixes,
        "method_keys": DEFAULT_CONTRACT_METHOD_KEYS,
        "summary": summary,
        "records": records,
        "objective_inputs_exclude": [
            "true_answer",
            "clean_label",
            "gold_rationale",
            "task_id-specific rules",
        ],
        "diagnostic_note": (
            "true_answer appears only in diagnostics after scoring; it is not used by rank_task_variants "
            "or score_contract_features."
        ),
    }
    write_json(args.summary_json, payload)
    write_text(args.output_md, format_markdown_report(summary))
    if args.selector_output_jsonl or args.selector_summary_json or args.selector_report_md:
        selector_records = build_objective_selector_records(
            prefixes,
            args.base_dir,
            min_top_score=args.min_top_score,
            min_score_margin=args.min_score_margin,
        )
        selector_summary = summarize_selector_records(selector_records)
        audit_files = args.audit_files or default_audit_files(args.base_dir, prefixes)
        audit_summary = None
        if audit_files:
            from experiment.aqua.contract_ablation_analysis import load_audit_labels

            audit_summary = summarize_selector_records_with_audit(
                selector_records,
                load_audit_labels(audit_files),
            )
        if args.selector_output_jsonl:
            write_jsonl(args.selector_output_jsonl, selector_records)
        if args.selector_summary_json:
            write_json(
                args.selector_summary_json,
                {
                    "prefixes": prefixes,
                    "min_top_score": args.min_top_score,
                    "min_score_margin": args.min_score_margin,
                    "summary": selector_summary,
                    "audit_files": audit_files,
                    "posthoc_audit_summary": audit_summary,
                    "diagnostic_note": (
                        "This selector is label-free at selection time, but the summary uses true_answer "
                        "for post-hoc evaluation."
                    ),
                },
            )
        if args.selector_report_md:
            write_text(
                args.selector_report_md,
                format_selector_report(
                    selector_summary,
                    audit_summary,
                    min_score_margin=args.min_score_margin,
                ),
            )
    print(json.dumps({"output_md": args.output_md, "summary_json": args.summary_json}, indent=2))


if __name__ == "__main__":
    main()
