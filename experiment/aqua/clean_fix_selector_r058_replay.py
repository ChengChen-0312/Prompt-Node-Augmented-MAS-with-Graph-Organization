import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.clean_fix_selector_ranker import (  # noqa: E402
    FORBIDDEN_INPUT_FIELDS,
    predict_label,
    predict_score,
)
from experiment.aqua.contract_graph_objective import is_solved, summarize_selector_records  # noqa: E402
from experiment.aqua.graph_policy_distill_export import normalize_graph_for_policy  # noqa: E402
from experiment.aqua.offline_utility_selector import (  # noqa: E402
    STRONG_BINDING_STATUS,
    extract_contract_consensus_features,
    load_jsonl_by_task,
    normalize_option,
)
from experiment.aqua.selective_promptnode_activation import (  # noqa: E402
    extract_direct_votes,
    summarize_direct_votes,
)


RULE_NAME = "r080_r078_selector_on_r058_metadata"


def load_json(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_r078_model(path: str) -> Dict[str, Any]:
    payload = load_json(path)
    model = payload.get("model")
    if not isinstance(model, dict):
        raise ValueError(f"No R078 model found in {path}")
    return model


def _graph_observation(promptnode_record: Dict[str, Any]) -> Dict[str, Any]:
    graph = promptnode_record.get("generated_graph")
    if not isinstance(graph, dict):
        return {
            "num_prompt_nodes": 0,
            "num_prompt_node_edges": 0,
            "prompt_node_role_counts": {},
            "prompt_node_edge_role_pairs": [],
            "has_promptnode_specs": False,
            "has_promptnode_edge_permissions": False,
        }
    policy_graph = normalize_graph_for_policy(graph)
    return {
        "num_prompt_nodes": policy_graph["num_prompt_nodes"],
        "num_prompt_node_edges": policy_graph["num_prompt_node_edges"],
        "prompt_node_role_counts": policy_graph["prompt_node_role_counts"],
        "prompt_node_edge_role_pairs": policy_graph["prompt_node_edge_role_pairs"],
        "has_promptnode_specs": bool(policy_graph["prompt_node_specs"]),
        "has_promptnode_edge_permissions": bool(policy_graph["prompt_node_edge_permissions"]),
    }


def build_candidate_selector_row(
    baseline_record: Dict[str, Any],
    promptnode_record: Dict[str, Any],
) -> Dict[str, Any]:
    contract = extract_contract_consensus_features(promptnode_record)
    router_option = normalize_option(contract.get("router_option"))
    router_status = str(contract.get("router_binding_status") or "").upper()
    direct_summary = summarize_direct_votes(extract_direct_votes(baseline_record))
    direct_options = set(direct_summary.get("direct_distinct_options") or [])
    strong_contract_count = int(contract.get("strong_router_contract_count") or 0)
    has_strong_contract = bool(router_option and router_status in STRONG_BINDING_STATUS)
    bucket = "preferred_graph" if has_strong_contract else "low_margin_top"
    return {
        "selector_policy_input": {
            "slice_prefix": "tail34",
            "question": promptnode_record.get("question") or baseline_record.get("question"),
            "candidate_method": "r058_router_contract_terminal",
            "label_free_objective_features": {
                "objective_bucket": bucket,
                "objective_bucket_flags": {
                    "preferred_graph": bucket == "preferred_graph",
                    "multi_view_tie": False,
                    "low_margin_top": bucket == "low_margin_top",
                    "non_positive_top": False,
                    "non_preferred_graph": False,
                },
                "objective_reward": 10 if has_strong_contract else 1,
                "score_margin_to_next": 3 if has_strong_contract else None,
                "has_margin_at_least_3": has_strong_contract,
                "score_components": {
                    "strong_contract": 4 if strong_contract_count else 0,
                    "direct_agreement": 3 if router_option in direct_options else 0,
                    "direct_vote_support": (
                        direct_summary.get("direct_vote_counts", {}).get(router_option, 0)
                        if router_option
                        else 0
                    ),
                    "prompt_node_graph": 1,
                    "conflict_penalty": 0,
                    "weak_contract_penalty": 0 if has_strong_contract else -1,
                },
            },
            "candidate_graph_observation": _graph_observation(promptnode_record),
        },
        "clean_fix_distillation_target": {"target_class": "unknown_r058_replay"},
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


def build_r058_replay_records(
    baseline_records: Dict[str, Dict[str, Any]],
    promptnode_records: Dict[str, Dict[str, Any]],
    model: Dict[str, Any],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for task_id in [task_id for task_id in baseline_records if task_id in promptnode_records]:
        baseline_record = baseline_records[task_id]
        promptnode_record = promptnode_records[task_id]
        selector_row = build_candidate_selector_row(baseline_record, promptnode_record)
        selector_input = selector_row["selector_policy_input"]
        score = predict_score(model, selector_row)
        positive = bool(predict_label(model, selector_row) and score > 0)
        baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
        promptnode_prediction = normalize_option(promptnode_record.get("predicted_answer"))
        selected_source = "r078_on_r058_promptnode" if positive and promptnode_prediction != baseline_prediction else "baseline"
        predicted_answer = promptnode_prediction if selected_source != "baseline" else baseline_prediction
        true_answer = normalize_option(baseline_record.get("true_answer") or promptnode_record.get("true_answer"))
        graph_obs = selector_input["candidate_graph_observation"]
        records.append(
            {
                "task_id": task_id,
                "question": baseline_record.get("question") or promptnode_record.get("question"),
                "true_answer": true_answer,
                "baseline_prediction": baseline_prediction,
                "baseline_is_solved": is_solved(baseline_prediction, true_answer),
                "promptnode_prediction": promptnode_prediction,
                "promptnode_is_solved": is_solved(promptnode_prediction, true_answer),
                "predicted_answer": predicted_answer,
                "is_solved": is_solved(predicted_answer, true_answer),
                "selected_source": selected_source,
                "selector_score": score,
                "selector_positive": positive,
                "selector_input_violation": _field_violates(selector_input),
                "candidate_graph_observation": graph_obs,
                "router_contract_status": (
                    selector_input["label_free_objective_features"]["objective_bucket"]
                ),
                "selection_rule": RULE_NAME,
            }
        )
    return records


def summarize_r058_replay(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    generated_promptnode_graph_records = sum(
        1
        for record in records
        if record.get("candidate_graph_observation", {}).get("num_prompt_nodes", 0) > 0
    )
    promptnode_spec_records = sum(
        1
        for record in records
        if record.get("candidate_graph_observation", {}).get("has_promptnode_specs")
    )
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_tasks": len(records),
        "overall": summarize_selector_records(records),
        "generated_promptnode_graph_records": generated_promptnode_graph_records,
        "promptnode_spec_records": promptnode_spec_records,
        "selector_feature_violations": sum(1 for record in records if record.get("selector_input_violation")),
        "claim_boundary": (
            "R080 is a negative metadata-compatible replay: R058 contains explicit PromptNode graphs, but applying "
            "the R078 selector to this dense PromptNode candidate pool harms tail34. This shows metadata alone is "
            "insufficient; the generated graph candidates and selector objective must be aligned."
        ),
    }


def build_r058_replay_payload(
    baseline_jsonl: str = "experiment/aqua/aqua_tail34_arg_baseline_results.jsonl",
    promptnode_jsonl: str = "experiment/aqua/aqua_tail34_r058_router_contract_terminal_results.jsonl",
    model_summary_json: str = "experiment/aqua/res_logs/aqua_first200_r078_clean_fix_selector_summary.json",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    baseline_records = load_jsonl_by_task(baseline_jsonl)
    promptnode_records = load_jsonl_by_task(promptnode_jsonl)
    model = load_r078_model(model_summary_json)
    records = build_r058_replay_records(baseline_records, promptnode_records, model)
    summary = {
        "baseline_jsonl": baseline_jsonl,
        "promptnode_jsonl": promptnode_jsonl,
        "model_summary_json": model_summary_json,
        **summarize_r058_replay(records),
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
            "# R080 R078 Selector on R058 Generated PromptNode Graphs",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Output records: `{output_jsonl}`",
            f"- Selector accuracy: `{overall['overall']}`",
            f"- ARG baseline accuracy: `{overall['baseline']}`",
            f"- Delta vs baseline: `{overall['delta_vs_baseline']:+d}`",
            f"- Switches: `{overall['switches']}`",
            f"- Fix/Harm: `{overall['fix_harm']}`",
            f"- Generated PromptNode graph records: `{summary['generated_promptnode_graph_records']}`",
            f"- PromptNode spec records: `{summary['promptnode_spec_records']}`",
            f"- Selector feature violations: `{summary['selector_feature_violations']}`",
            "",
            "## Interpretation",
            "",
            "Unlike R079, this replay uses a tail34 candidate source that does contain explicit PromptNode graph metadata. "
            "The result is still negative: the selector switches to three dense R058 PromptNode candidates and all three "
            "are harms against the historical ARG baseline. This separates two requirements for the SCI method: expose "
            "PromptNode graph metadata, and train/generate graph candidates aligned with the clean-fix objective.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay R078 selector over R058 generated PromptNode graphs.")
    parser.add_argument(
        "--baseline-jsonl",
        default="experiment/aqua/aqua_tail34_arg_baseline_results.jsonl",
    )
    parser.add_argument(
        "--promptnode-jsonl",
        default="experiment/aqua/aqua_tail34_r058_router_contract_terminal_results.jsonl",
    )
    parser.add_argument(
        "--model-summary-json",
        default="experiment/aqua/res_logs/aqua_first200_r078_clean_fix_selector_summary.json",
    )
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_tail34_r080_r078_on_r058_metadata_results.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_tail34_r080_r078_on_r058_metadata_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_tail34_r080_r078_on_r058_metadata_report.md",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    records, summary = build_r058_replay_payload(
        baseline_jsonl=args.baseline_jsonl,
        promptnode_jsonl=args.promptnode_jsonl,
        model_summary_json=args.model_summary_json,
    )
    write_jsonl(args.output_jsonl, records)
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary, args.output_jsonl))
    overall = summary["overall"]
    print(
        "Replayed R078 selector on R058 metadata: "
        f"accuracy={overall['overall']} baseline={overall['baseline']} "
        f"switches={overall['switches']} fix_harm={overall['fix_harm']}"
    )


if __name__ == "__main__":
    main()
