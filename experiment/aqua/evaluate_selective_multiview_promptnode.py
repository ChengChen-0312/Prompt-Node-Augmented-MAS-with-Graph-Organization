import argparse
import asyncio
import datetime
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from sentence_transformers import SentenceTransformer


os.environ["TOKENIZERS_PARALLELISM"] = "false"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AQUA_DIR = os.path.dirname(__file__)
for path in (REPO_ROOT, AQUA_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from experiment.aqua.aqua_prompt_set import ROLE_DESCRIPTION  # noqa: E402
from experiment.aqua.contract_ablation_analysis import (  # noqa: E402
    load_audit_labels,
    summarize_variant_records,
)
from experiment.aqua.contract_graph_objective import (  # noqa: E402
    score_contract_features,
    select_objective_guided_prediction,
)
from experiment.aqua.evaluate_aqua import (  # noqa: E402
    assert_llm_environment_ready,
    assert_valid_evaluation_run,
)
from experiment.aqua.evaluate_selective_promptnode import (  # noqa: E402
    load_aqua_tasks,
    load_model_with_workdir,
    run_graph_record,
)
from experiment.aqua.finetune_aqua import setup_environment  # noqa: E402
from experiment.aqua.offline_utility_selector import (  # noqa: E402
    DEFAULT_CONTRACT_METHOD_KEYS,
    extract_contract_consensus_features,
    graph_has_prompt_node,
    normalize_option,
)
from experiment.aqua.selective_multiview_trigger import (  # noqa: E402
    extract_multiview_trigger_features,
    ratio_text,
    should_run_multiview,
    write_json,
    write_jsonl,
    write_text,
)
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens  # noqa: E402

import mas_framework.agents.final_decision  # noqa: E402,F401
import mas_framework.prompt.AQuA_prompt_set  # noqa: E402,F401


RULE_NAME = "r069_integrated_selective_multiview_promptnode"
BOUNDARY = "fresh_integrated_selective_multiview_promptnode_run"

DEFAULT_VIEW_CONFIGS = [
    {
        "method_key": "router",
        "decision_method": "RouterContractFinalRefer",
        "num_candidate_graphs": 1,
        "decision_exposure_policy": "auto",
    },
    {
        "method_key": "candidate",
        "decision_method": "RouterContractFinalRefer",
        "num_candidate_graphs": 4,
        "decision_exposure_policy": "auto",
    },
    {
        "method_key": "conservative",
        "decision_method": "ConservativeRouterContractFinalRefer",
        "num_candidate_graphs": 1,
        "decision_exposure_policy": "auto",
    },
    {
        "method_key": "calibrated",
        "decision_method": "CalibratedPNUtilityFinalRefer",
        "num_candidate_graphs": 1,
        "decision_exposure_policy": "auto",
    },
]


def _method_order(view_configs: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    if view_configs is None:
        return [config["method_key"] for config in DEFAULT_VIEW_CONFIGS]
    return [config["method_key"] for config in view_configs]


def rank_runtime_variants(
    view_records: Dict[str, Dict[str, Any]],
    method_keys: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    ranked = []
    for index, method_key in enumerate(method_keys or DEFAULT_CONTRACT_METHOD_KEYS):
        record = view_records.get(method_key)
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


def _selected_method(
    selected_prediction: Optional[str],
    selected_source: str,
    ranked_variants: List[Dict[str, Any]],
) -> Optional[str]:
    if selected_source == "baseline" or not ranked_variants:
        return None
    top_score = ranked_variants[0]["score"]
    for variant in ranked_variants:
        if variant.get("score") != top_score:
            continue
        candidate = normalize_option(variant.get("router_option")) or normalize_option(
            variant.get("predicted_answer")
        )
        if candidate == selected_prediction:
            return variant.get("method_key")
    return ranked_variants[0].get("method_key")


def _record_by_selected_source(
    selected_source: str,
    selected_method: Optional[str],
    baseline_record: Dict[str, Any],
    view_records: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    if selected_source != "baseline" and selected_method in view_records:
        return view_records[selected_method]
    return baseline_record


def run_task_selective_multiview(
    task: Dict[str, Any],
    baseline_runner: Callable[[Dict[str, Any]], Dict[str, Any]],
    view_runner: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    view_configs: Optional[List[Dict[str, Any]]] = None,
    min_top_score: int = 1,
    min_score_margin: int = 0,
) -> Dict[str, Any]:
    view_configs = view_configs or DEFAULT_VIEW_CONFIGS
    baseline_record = baseline_runner(task)
    trigger_features = extract_multiview_trigger_features(baseline_record)
    multiview_was_run = should_run_multiview(trigger_features)
    view_records: Dict[str, Dict[str, Any]] = {}
    ranked_variants: List[Dict[str, Any]] = []

    baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
    if multiview_was_run:
        for config in view_configs:
            view_records[config["method_key"]] = view_runner(task, config)
        ranked_variants = rank_runtime_variants(view_records, _method_order(view_configs))
        selected_prediction, selected_source = select_objective_guided_prediction(
            baseline_prediction,
            ranked_variants,
            min_top_score=min_top_score,
            min_score_margin=min_score_margin,
        )
    else:
        selected_prediction, selected_source = baseline_prediction, "baseline"

    selected_method = _selected_method(selected_prediction, selected_source, ranked_variants)
    selected_record = _record_by_selected_source(
        selected_source,
        selected_method,
        baseline_record,
        view_records,
    )
    true_answer = normalize_option(baseline_record.get("true_answer") or task.get("answer"))
    return {
        "task_id": task.get("task_id") or baseline_record.get("task_id"),
        "question": baseline_record.get("question") or task.get("task"),
        "true_answer": true_answer,
        "predicted_answer": selected_prediction,
        "raw_response": selected_record.get("raw_response"),
        "is_solved": selected_prediction == true_answer,
        "selected_source": selected_source,
        "selected_method": selected_method,
        "selection_rule": RULE_NAME,
        "min_top_score": min_top_score,
        "min_score_margin": min_score_margin,
        "multiview_was_run": multiview_was_run,
        "baseline_prediction": baseline_prediction,
        "baseline_is_solved": baseline_prediction == true_answer,
        "view_predictions": {
            key: normalize_option(record.get("predicted_answer"))
            for key, record in view_records.items()
        },
        "view_records": view_records,
        "ranked_variants": ranked_variants,
        "top_score": ranked_variants[0]["score"] if ranked_variants else None,
        "trigger_features": trigger_features,
    }


async def run_task_selective_multiview_async(
    task: Dict[str, Any],
    graph_index: int,
    baseline_model,
    promptnode_model,
    sentence_model: SentenceTransformer,
    role_constraints_dict: Dict[str, str],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    baseline_record = await run_graph_record(
        task,
        baseline_model,
        sentence_model,
        role_constraints_dict,
        graph_index,
        llm_name=args.llm_name,
        decision_method=args.baseline_decision_method,
        prompt_node_policy="none",
        prompt_node_topology_policy="none",
        decision_exposure_policy="all",
        num_candidate_graphs=args.baseline_num_candidate_graphs,
    )
    trigger_features = extract_multiview_trigger_features(baseline_record)
    if not should_run_multiview(trigger_features):
        true_answer = normalize_option(baseline_record.get("true_answer") or task.get("answer"))
        baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
        return {
            "task_id": task.get("task_id"),
            "question": baseline_record.get("question") or task.get("task"),
            "true_answer": true_answer,
            "predicted_answer": baseline_prediction,
            "raw_response": baseline_record.get("raw_response"),
            "is_solved": baseline_prediction == true_answer,
            "selected_source": "baseline",
            "selected_method": None,
            "selection_rule": RULE_NAME,
            "min_top_score": args.min_top_score,
            "min_score_margin": args.min_score_margin,
            "multiview_was_run": False,
            "baseline_prediction": baseline_prediction,
            "baseline_is_solved": baseline_prediction == true_answer,
            "view_predictions": {},
            "view_records": {},
            "ranked_variants": [],
            "top_score": None,
            "trigger_features": trigger_features,
            "baseline_record": baseline_record,
        }

    async def run_view(config: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        method_key = config["method_key"]
        try:
            record = await run_graph_record(
                task,
                promptnode_model,
                sentence_model,
                role_constraints_dict,
                graph_index,
                llm_name=args.llm_name,
                decision_method=config["decision_method"],
                prompt_node_policy="none",
                prompt_node_topology_policy=args.prompt_node_topology_policy,
                decision_exposure_policy=config.get("decision_exposure_policy", "auto"),
                num_candidate_graphs=int(config.get("num_candidate_graphs", 1)),
            )
            return method_key, record
        except Exception as exc:
            return method_key, {
                "task_id": task.get("task_id"),
                "question": task.get("task"),
                "true_answer": task.get("answer"),
                "predicted_answer": None,
                "raw_response": None,
                "is_solved": False,
                "agent_outputs": [],
                "generated_graph": {},
                "error": str(exc),
            }

    view_items = await asyncio.gather(*(run_view(config) for config in DEFAULT_VIEW_CONFIGS))
    view_records = {method_key: record for method_key, record in view_items}

    def baseline_runner(_task: Dict[str, Any]) -> Dict[str, Any]:
        return baseline_record

    def view_runner(_task: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        return view_records[config["method_key"]]

    record = run_task_selective_multiview(
        task,
        baseline_runner,
        view_runner,
        view_configs=DEFAULT_VIEW_CONFIGS,
        min_top_score=args.min_top_score,
        min_score_margin=args.min_score_margin,
    )
    record["baseline_record"] = baseline_record
    return record


def summarize_integrated_multiview_records(
    records: List[Dict[str, Any]],
    audit_labels: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    total = len(records)
    solved = sum(1 for record in records if record.get("is_solved"))
    baseline = sum(1 for record in records if record.get("baseline_is_solved"))
    run_records = [record for record in records if record.get("multiview_was_run")]
    switch_records = [record for record in records if record.get("selected_source") != "baseline"]
    fixes = [
        record
        for record in records
        if not record.get("baseline_is_solved") and record.get("is_solved")
    ]
    harms = [
        record
        for record in records
        if record.get("baseline_is_solved") and not record.get("is_solved")
    ]
    posthoc = summarize_variant_records(RULE_NAME, records, audit_labels) if audit_labels else {}
    return {
        "rule": RULE_NAME,
        "total_tasks": total,
        "solved_tasks": solved,
        "baseline_solved_tasks": baseline,
        "overall": ratio_text(solved, total),
        "baseline": ratio_text(baseline, total),
        "delta_vs_baseline": solved - baseline,
        "multiview_run_count": len(run_records),
        "multiview_run": ratio_text(len(run_records), total),
        "switches": len(switch_records),
        "fixes": len(fixes),
        "harms": len(harms),
        "fix_harm": f"{len(fixes)}/{len(harms)}",
        "run_tasks": [record["task_id"] for record in run_records],
        "switch_tasks": [record["task_id"] for record in switch_records],
        "fix_tasks": [record["task_id"] for record in fixes],
        "harm_tasks": [record["task_id"] for record in harms],
        "posthoc_audit_summary": posthoc,
        **{
            key: posthoc[key]
            for key in [
                "clean",
                "noisy_or_ambiguous",
                "clean_fix_harm",
                "noisy_fix_harm",
            ]
            if key in posthoc
        },
    }


def render_report(summary: Dict[str, Any], records: List[Dict[str, Any]]) -> str:
    run_lines = []
    for record in records:
        if not record.get("multiview_was_run"):
            continue
        reasons = [
            name
            for name in ["r063_trigger", "missing_direct_vote_trigger"]
            if record.get("trigger_features", {}).get(name)
        ]
        run_lines.append(
            "| {task} | {base} | {selected} | {source} | {method} | {score} | {reasons} | {solved} |".format(
                task=record.get("task_id"),
                base=record.get("baseline_prediction"),
                selected=record.get("predicted_answer"),
                source=record.get("selected_source"),
                method=record.get("selected_method"),
                score=record.get("top_score"),
                reasons=",".join(reasons),
                solved=record.get("is_solved"),
            )
        )
    if not run_lines:
        run_lines.append("| none | - | - | - | - | - | - | - |")

    clean_lines = []
    if summary.get("clean"):
        clean_lines = [
            f"- Clean: `{summary.get('clean')}`",
            f"- Clean Fix/Harm: `{summary.get('clean_fix_harm')}`",
            f"- Noisy/Ambiguous: `{summary.get('noisy_or_ambiguous')}`",
            f"- Noisy/Ambiguous Fix/Harm: `{summary.get('noisy_fix_harm')}`",
        ]
    return "\n".join(
        [
            "# R069 Fresh Integrated Selective Multi-View PromptNode",
            "",
            f"**Boundary**: `{BOUNDARY}`. This run executes ARG first, triggers multi-view PromptNodes online, and applies the label-free objective selector.",
            "",
            "## Summary",
            "",
            f"- Selected accuracy: `{summary['overall']}`",
            f"- ARG baseline inside R069: `{summary['baseline']}`",
            f"- Delta vs baseline: `{summary['delta_vs_baseline']:+d}`",
            f"- Multi-view runs: `{summary['multiview_run']}`",
            f"- Switches: `{summary['switches']}`",
            f"- Fix/Harm: `{summary['fix_harm']}`",
            *clean_lines,
            f"- Cost: `${summary.get('cost', 0.0):.6f}`",
            f"- Prompt tokens: `{int(summary.get('prompt_tokens', 0))}`",
            f"- Completion tokens: `{int(summary.get('completion_tokens', 0))}`",
            "",
            "## Triggered Tasks",
            "",
            "| Task | ARG | Selected | Source | Method | Top score | Trigger reasons | Solved |",
            "| --- | ---: | ---: | --- | --- | ---: | --- | --- |",
            *run_lines,
            "",
            "## Interpretation",
            "",
            "This is the prospective counterpart to R068. The trigger excludes true answers, correctness, clean/noisy labels, and task-id-specific rules. Post-hoc accuracy and audit splits are diagnostics only.",
            "",
        ]
    )


def _absolute(path: Optional[str]) -> Optional[str]:
    if path is None:
        return None
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(REPO_ROOT, path))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fresh integrated selective multi-view PromptNode evaluator for AQuA."
    )
    parser.add_argument("--baseline-model-path", required=True)
    parser.add_argument("--promptnode-model-path", required=True)
    parser.add_argument("--dataset-path", default="datasets/AQuA/AQuA.jsonl")
    parser.add_argument("--task-split-path", default="experiment/aqua/task_split_aqua_tail34.json")
    parser.add_argument("--split-name", default="tail34")
    parser.add_argument("--llm-name", default="gpt-4o-2024-08-06")
    parser.add_argument("--baseline-decision-method", default="FinalRefer")
    parser.add_argument("--baseline-num-candidate-graphs", type=int, default=1)
    parser.add_argument("--prompt-node-topology-policy", default="canonicalize_generated")
    parser.add_argument("--min-top-score", type=int, default=1)
    parser.add_argument("--min-score-margin", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--audit-file", default="experiment/aqua/aqua_tail34_option_binding_audit.jsonl")
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--summary-log-file", default=None)
    parser.add_argument("--report-md", required=True)
    return parser


def absolutize_args(args: argparse.Namespace) -> argparse.Namespace:
    for attr in (
        "baseline_model_path",
        "promptnode_model_path",
        "dataset_path",
        "task_split_path",
        "audit_file",
        "output_file",
        "summary_json",
        "summary_log_file",
        "report_md",
    ):
        setattr(args, attr, _absolute(getattr(args, attr, None)))
    return args


async def main_async() -> None:
    args = absolutize_args(build_arg_parser().parse_args())
    assert_llm_environment_ready(args.llm_name)
    setup_environment(42)
    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    print("Loading baseline and PromptNode models...")
    baseline_model = load_model_with_workdir(args.baseline_model_path, ef=True)
    promptnode_model = load_model_with_workdir(args.promptnode_model_path, ef=True)
    baseline_model.eval()
    promptnode_model.eval()
    sentence_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    role_constraints_dict = ROLE_DESCRIPTION
    tasks = load_aqua_tasks(args.dataset_path, args.task_split_path, args.limit)
    print(f"Loaded {len(tasks)} AQuA tasks for integrated selective multi-view evaluation.")

    records: List[Dict[str, Any]] = []
    for graph_index, task in enumerate(tasks):
        try:
            record = await run_task_selective_multiview_async(
                task,
                graph_index,
                baseline_model,
                promptnode_model,
                sentence_model,
                role_constraints_dict,
                args,
            )
        except Exception as exc:
            print(f"Error executing task {task.get('task_id')}: {exc}")
            record = {
                "task_id": task.get("task_id"),
                "question": task.get("task"),
                "true_answer": task.get("answer"),
                "predicted_answer": None,
                "raw_response": None,
                "is_solved": False,
                "selected_source": "error",
                "selected_method": None,
                "selection_rule": RULE_NAME,
                "multiview_was_run": False,
                "baseline_prediction": None,
                "baseline_is_solved": False,
                "view_predictions": {},
                "view_records": {},
                "ranked_variants": [],
                "trigger_features": {},
                "error": str(exc),
            }
        records.append(record)
        write_jsonl(args.output_file, records)
        current = summarize_integrated_multiview_records(records)
        print(
            "R069 progress: "
            f"{current['overall']} baseline={current['baseline']} "
            f"runs={current['multiview_run']} switches={current['switches']}"
        )

    prompt_tokens = PromptTokens.instance().value
    completion_tokens = CompletionTokens.instance().value
    assert_valid_evaluation_run(
        records,
        total_tasks=len(tasks),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    audit_labels = {}
    if args.audit_file and os.path.exists(args.audit_file):
        audit_labels = load_audit_labels([args.audit_file])
    summary = summarize_integrated_multiview_records(records, audit_labels=audit_labels)
    summary.update(
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "boundary": BOUNDARY,
            "split_name": args.split_name,
            "llm_name": args.llm_name,
            "baseline_model_path": args.baseline_model_path,
            "promptnode_model_path": args.promptnode_model_path,
            "output_file": args.output_file,
            "view_configs": DEFAULT_VIEW_CONFIGS,
            "cost": Cost.instance().value,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "trigger_excludes": [
                "true_answer",
                "is_solved",
                "clean_label",
                "audit_label",
                "task_id-specific rules",
            ],
        }
    )
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary, records))
    if args.summary_log_file:
        parent = os.path.dirname(args.summary_log_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(args.summary_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
