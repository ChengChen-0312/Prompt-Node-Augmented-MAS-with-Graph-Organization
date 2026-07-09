import argparse
import asyncio
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

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
from experiment.aqua.contract_graph_objective import select_objective_guided_prediction  # noqa: E402
from experiment.aqua.evaluate_aqua import (  # noqa: E402
    assert_llm_environment_ready,
    assert_valid_evaluation_run,
)
from experiment.aqua.evaluate_selective_multiview_promptnode import (  # noqa: E402
    load_aqua_tasks,
    load_model_with_workdir,
    rank_runtime_variants,
    run_graph_record,
)
from experiment.aqua.finetune_aqua import setup_environment  # noqa: E402
from experiment.aqua.offline_utility_selector import normalize_option  # noqa: E402
from experiment.aqua.selective_multiview_trigger import (  # noqa: E402
    extract_multiview_trigger_features,
    ratio_text,
    should_run_multiview,
    write_json,
    write_jsonl,
    write_text,
)
from experiment.aqua.surgical_cascade_trigger_replay import (  # noqa: E402
    should_run_surgical_trigger,
)
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens  # noqa: E402

import mas_framework.agents.final_decision  # noqa: E402,F401
import mas_framework.prompt.AQuA_prompt_set  # noqa: E402,F401


RULE_NAME = "r072_fresh_integrated_cascade_multiview_promptnode"
BOUNDARY = "fresh_integrated_cascade_multiview_promptnode_run"
VALID_OPTIONS = {"A", "B", "C", "D", "E"}
TRIGGER_POLICIES = {"r068": "r068", "r073_surgical": "r073_surgical"}

DEFAULT_CASCADE_VIEW_CONFIGS = [
    {
        "method_key": "router",
        "decision_method": "RouterContractFinalRefer",
        "num_candidate_graphs": 1,
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
    {
        "method_key": "candidate",
        "decision_method": "RouterContractFinalRefer",
        "num_candidate_graphs": 4,
        "decision_exposure_policy": "auto",
    },
]


def _option_counts(predictions: Iterable[Any]) -> Counter:
    return Counter(
        option
        for option in (normalize_option(prediction) for prediction in predictions)
        if option in VALID_OPTIONS
    )


def _selected_method(
    selected_prediction: Optional[str],
    ranked_variants: List[Dict[str, Any]],
) -> Optional[str]:
    if selected_prediction not in VALID_OPTIONS or not ranked_variants:
        return None
    top_score = ranked_variants[0]["score"]
    for variant in ranked_variants:
        if variant.get("score") != top_score:
            continue
        option = normalize_option(variant.get("router_option")) or normalize_option(
            variant.get("predicted_answer")
        )
        if option == selected_prediction:
            return variant.get("method_key")
    return ranked_variants[0].get("method_key")


def _method_order(view_configs: List[Dict[str, Any]]) -> List[str]:
    return [config["method_key"] for config in view_configs]


def should_run_cascade_trigger(features: Dict[str, Any], trigger_policy: str = "r068") -> bool:
    if trigger_policy == "r073_surgical":
        return should_run_surgical_trigger(features)
    if trigger_policy == "r068":
        return should_run_multiview(features)
    raise ValueError(f"Unknown trigger policy: {trigger_policy}")


def effective_rule_name(trigger_policy: str = "r068") -> str:
    if trigger_policy == "r073_surgical":
        return "r074_fresh_integrated_surgical_cascade_promptnode"
    return RULE_NAME


def _build_baseline_record(
    task: Dict[str, Any],
    baseline_record: Dict[str, Any],
    trigger_features: Dict[str, Any],
    trigger_policy: str = "r068",
) -> Dict[str, Any]:
    true_answer = normalize_option(baseline_record.get("true_answer") or task.get("answer"))
    baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
    return {
        "task_id": task.get("task_id") or baseline_record.get("task_id"),
        "question": baseline_record.get("question") or task.get("task"),
        "true_answer": true_answer,
        "predicted_answer": baseline_prediction,
        "raw_response": baseline_record.get("raw_response"),
        "is_solved": baseline_prediction == true_answer,
        "selected_source": "baseline",
        "selected_method": None,
        "selection_rule": RULE_NAME,
        "multiview_was_run": False,
        "baseline_prediction": baseline_prediction,
        "baseline_is_solved": baseline_prediction == true_answer,
        "view_predictions": {},
        "view_records": {},
        "ranked_seen_variants": [],
        "view_calls": 0,
        "full_view_count": 0,
        "trigger_features": trigger_features,
        "decision_features": {
            "rule": RULE_NAME,
            "trigger_policy": trigger_policy,
            "baseline_prediction": baseline_prediction,
            "seen_methods": [],
            "seen_predictions": [],
            "view_prediction_counts": {},
            "stopped_after_method": None,
        },
        "baseline_record": baseline_record,
    }


def run_task_cascade_multiview(
    task: Dict[str, Any],
    baseline_runner: Callable[[Dict[str, Any]], Dict[str, Any]],
    view_runner: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    view_configs: Optional[List[Dict[str, Any]]] = None,
    baseline_accept_support: int = 2,
    switch_support_valid_baseline: int = 2,
    switch_support_invalid_baseline: int = 3,
    min_views_before_decision: int = 2,
    trigger_policy: str = "r068",
) -> Dict[str, Any]:
    view_configs = view_configs or DEFAULT_CASCADE_VIEW_CONFIGS
    baseline_record = baseline_runner(task)
    trigger_features = extract_multiview_trigger_features(baseline_record)
    if not should_run_cascade_trigger(trigger_features, trigger_policy):
        return _build_baseline_record(task, baseline_record, trigger_features, trigger_policy)

    true_answer = normalize_option(baseline_record.get("true_answer") or task.get("answer"))
    baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
    selected_prediction = baseline_prediction
    selected_source = "baseline"
    selected_method = None
    selected_record = baseline_record
    view_records: Dict[str, Dict[str, Any]] = {}
    seen_predictions: List[Optional[str]] = []
    ranked_seen: List[Dict[str, Any]] = []
    stopped_after_method = None

    for config in view_configs:
        method_key = config["method_key"]
        record = view_runner(task, config)
        view_records[method_key] = record
        seen_predictions.append(normalize_option(record.get("predicted_answer")))
        stopped_after_method = method_key

        if len(seen_predictions) < min_views_before_decision:
            continue

        counts = _option_counts(seen_predictions)
        if (
            baseline_prediction in VALID_OPTIONS
            and counts.get(baseline_prediction, 0) >= baseline_accept_support
        ):
            selected_prediction = baseline_prediction
            selected_source = "baseline_early_accept"
            selected_method = None
            selected_record = baseline_record
            break

        ranked_seen = rank_runtime_variants(
            view_records,
            [method for method in _method_order(view_configs) if method in view_records],
        )
        candidate_prediction, candidate_source = select_objective_guided_prediction(
            baseline_prediction,
            ranked_seen,
            min_top_score=1,
            min_score_margin=0,
        )
        support_threshold = (
            switch_support_invalid_baseline
            if baseline_prediction is None
            else switch_support_valid_baseline
        )
        if (
            candidate_source != "baseline"
            and candidate_prediction in VALID_OPTIONS
            and counts.get(candidate_prediction, 0) >= support_threshold
        ):
            selected_prediction = candidate_prediction
            selected_source = "cascade_objective"
            selected_method = _selected_method(candidate_prediction, ranked_seen)
            selected_record = view_records.get(selected_method, record)
            break

    decision_features = {
        "rule": RULE_NAME,
        "trigger_policy": trigger_policy,
        "cascade_order": _method_order(view_configs),
        "baseline_prediction": baseline_prediction,
        "seen_methods": list(view_records),
        "seen_predictions": seen_predictions,
        "view_prediction_counts": dict(_option_counts(seen_predictions)),
        "baseline_accept_support": baseline_accept_support,
        "switch_support_valid_baseline": switch_support_valid_baseline,
        "switch_support_invalid_baseline": switch_support_invalid_baseline,
        "min_views_before_decision": min_views_before_decision,
        "stopped_after_method": stopped_after_method,
    }
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
        "multiview_was_run": True,
        "baseline_prediction": baseline_prediction,
        "baseline_is_solved": baseline_prediction == true_answer,
        "view_predictions": {
            method: normalize_option(record.get("predicted_answer"))
            for method, record in view_records.items()
        },
        "view_records": view_records,
        "ranked_seen_variants": ranked_seen,
        "view_calls": len(view_records),
        "full_view_count": len(view_configs),
        "trigger_features": trigger_features,
        "decision_features": decision_features,
        "baseline_record": baseline_record,
    }


async def run_task_cascade_multiview_async(
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

    async def run_view(config: Dict[str, Any]) -> Dict[str, Any]:
        return await run_graph_record(
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

    view_cache: Dict[str, Dict[str, Any]] = {}

    def baseline_runner(_task: Dict[str, Any]) -> Dict[str, Any]:
        return baseline_record

    def view_runner(_task: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        method_key = config["method_key"]
        if method_key not in view_cache:
            raise RuntimeError(f"View {method_key} was requested before async execution.")
        return view_cache[method_key]

    trigger_features = extract_multiview_trigger_features(baseline_record)
    if not should_run_cascade_trigger(trigger_features, args.trigger_policy):
        return _build_baseline_record(task, baseline_record, trigger_features, args.trigger_policy)

    view_configs = DEFAULT_CASCADE_VIEW_CONFIGS
    true_answer = normalize_option(baseline_record.get("true_answer") or task.get("answer"))
    baseline_prediction = normalize_option(baseline_record.get("predicted_answer"))
    seen_predictions: List[Optional[str]] = []
    view_records: Dict[str, Dict[str, Any]] = {}
    ranked_seen: List[Dict[str, Any]] = []
    selected_prediction = baseline_prediction
    selected_source = "baseline"
    selected_method = None
    selected_record = baseline_record
    stopped_after_method = None

    for config in view_configs:
        method_key = config["method_key"]
        try:
            view_cache[method_key] = await run_view(config)
        except Exception as exc:
            view_cache[method_key] = {
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
        view_records[method_key] = view_cache[method_key]
        seen_predictions.append(normalize_option(view_cache[method_key].get("predicted_answer")))
        stopped_after_method = method_key

        if len(seen_predictions) < args.min_views_before_decision:
            continue

        counts = _option_counts(seen_predictions)
        if (
            baseline_prediction in VALID_OPTIONS
            and counts.get(baseline_prediction, 0) >= args.baseline_accept_support
        ):
            selected_prediction = baseline_prediction
            selected_source = "baseline_early_accept"
            break

        ranked_seen = rank_runtime_variants(
            view_records,
            [config_item["method_key"] for config_item in view_configs if config_item["method_key"] in view_records],
        )
        candidate_prediction, candidate_source = select_objective_guided_prediction(
            baseline_prediction,
            ranked_seen,
            min_top_score=1,
            min_score_margin=0,
        )
        support_threshold = (
            args.switch_support_invalid_baseline
            if baseline_prediction is None
            else args.switch_support_valid_baseline
        )
        if (
            candidate_source != "baseline"
            and candidate_prediction in VALID_OPTIONS
            and counts.get(candidate_prediction, 0) >= support_threshold
        ):
            selected_prediction = candidate_prediction
            selected_source = "cascade_objective"
            selected_method = _selected_method(candidate_prediction, ranked_seen)
            selected_record = view_records.get(selected_method, view_cache[method_key])
            break

    decision_features = {
        "rule": RULE_NAME,
        "trigger_policy": args.trigger_policy,
        "cascade_order": _method_order(view_configs),
        "baseline_prediction": baseline_prediction,
        "seen_methods": list(view_records),
        "seen_predictions": seen_predictions,
        "view_prediction_counts": dict(_option_counts(seen_predictions)),
        "baseline_accept_support": args.baseline_accept_support,
        "switch_support_valid_baseline": args.switch_support_valid_baseline,
        "switch_support_invalid_baseline": args.switch_support_invalid_baseline,
        "min_views_before_decision": args.min_views_before_decision,
        "stopped_after_method": stopped_after_method,
    }
    return {
        "task_id": task.get("task_id"),
        "question": baseline_record.get("question") or task.get("task"),
        "true_answer": true_answer,
        "predicted_answer": selected_prediction,
        "raw_response": selected_record.get("raw_response"),
        "is_solved": selected_prediction == true_answer,
        "selected_source": selected_source,
        "selected_method": selected_method,
        "selection_rule": RULE_NAME,
        "multiview_was_run": True,
        "baseline_prediction": baseline_prediction,
        "baseline_is_solved": baseline_prediction == true_answer,
        "view_predictions": {
            method: normalize_option(record.get("predicted_answer"))
            for method, record in view_records.items()
        },
        "view_records": view_records,
        "ranked_seen_variants": ranked_seen,
        "view_calls": len(view_records),
        "full_view_count": len(view_configs),
        "trigger_features": trigger_features,
        "decision_features": decision_features,
        "baseline_record": baseline_record,
    }


def summarize_cascade_integrated_records(
    records: List[Dict[str, Any]],
    audit_labels: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    audit_labels = audit_labels or {}
    total = len(records)
    solved = sum(1 for record in records if record.get("is_solved"))
    baseline = sum(1 for record in records if record.get("baseline_is_solved"))
    run_records = [record for record in records if record.get("multiview_was_run")]
    switch_records = [record for record in records if record.get("selected_source") == "cascade_objective"]
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
    view_calls = sum(int(record.get("view_calls", 0)) for record in records)
    full_view_count = sum(int(record.get("full_view_count", 0)) for record in records)
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
        "view_call_count": view_calls,
        "full_view_count": full_view_count,
        "view_calls": ratio_text(view_calls, full_view_count),
        "view_call_rate": view_calls / full_view_count if full_view_count else 0.0,
        "switches": len(switch_records),
        "switch_tasks": [record["task_id"] for record in switch_records],
        "fixes": len(fixes),
        "harms": len(harms),
        "fix_harm": f"{len(fixes)}/{len(harms)}",
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
    title = (
        "R074 Fresh Integrated Surgical Cascade PromptNode"
        if summary.get("trigger_policy") == "r073_surgical"
        else "R072 Fresh Integrated Cascade Multi-View PromptNode"
    )
    lines = []
    for record in records:
        if not record.get("multiview_was_run"):
            continue
        reasons = [
            name
            for name in ["r063_trigger", "missing_direct_vote_trigger"]
            if record.get("trigger_features", {}).get(name)
        ]
        lines.append(
            "| {task} | {base} | {selected} | {source} | {calls} | {method} | {reasons} | {solved} |".format(
                task=record.get("task_id"),
                base=record.get("baseline_prediction"),
                selected=record.get("predicted_answer"),
                source=record.get("selected_source"),
                calls=record.get("view_calls"),
                method=record.get("selected_method"),
                reasons=",".join(reasons),
                solved=record.get("is_solved"),
            )
        )
    if not lines:
        lines.append("| none | - | - | - | - | - | - | - |")
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
            f"# {title}",
            "",
            f"**Boundary**: `{BOUNDARY}`. This run executes cascade PromptNode views online and stops early when the rule fires.",
            "",
            "## Summary",
            "",
            f"- Selected accuracy: `{summary['overall']}`",
            f"- Internal ARG baseline: `{summary['baseline']}`",
            f"- Delta vs baseline: `{summary['delta_vs_baseline']:+d}`",
            f"- Multi-view triggered tasks: `{summary['multiview_run']}`",
            f"- View calls: `{summary['view_calls']}`",
            f"- Trigger policy: `{summary.get('trigger_policy', 'r068')}`",
            f"- Switches: `{summary['switches']}`",
            f"- Fix/Harm: `{summary['fix_harm']}`",
            *clean_lines,
            f"- Cost: `${summary.get('cost', 0.0):.6f}`",
            f"- Prompt tokens: `{int(summary.get('prompt_tokens', 0))}`",
            f"- Completion tokens: `{int(summary.get('completion_tokens', 0))}`",
            "",
            "## Triggered Tasks",
            "",
            "| Task | ARG | Selected | Source | View calls | Method | Trigger reasons | Solved |",
            "| --- | ---: | ---: | --- | ---: | --- | --- | --- |",
            *lines,
            "",
            "## Interpretation",
            "",
            "This fresh online cascade run excludes true answers, correctness fields, audit labels, and task-id-specific rules from trigger and cascade decisions.",
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
        description="Fresh integrated cascade multi-view PromptNode evaluator for AQuA."
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
    parser.add_argument("--trigger-policy", choices=sorted(TRIGGER_POLICIES), default="r068")
    parser.add_argument("--baseline-accept-support", type=int, default=2)
    parser.add_argument("--switch-support-valid-baseline", type=int, default=2)
    parser.add_argument("--switch-support-invalid-baseline", type=int, default=3)
    parser.add_argument("--min-views-before-decision", type=int, default=2)
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
    print(f"Loaded {len(tasks)} AQuA tasks for integrated cascade multi-view evaluation.")

    records: List[Dict[str, Any]] = []
    for graph_index, task in enumerate(tasks):
        try:
            record = await run_task_cascade_multiview_async(
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
                "ranked_seen_variants": [],
                "view_calls": 0,
                "full_view_count": 0,
                "trigger_features": {},
                "decision_features": {},
                "error": str(exc),
            }
        records.append(record)
        write_jsonl(args.output_file, records)
        current = summarize_cascade_integrated_records(records)
        print(
            "R072 progress: "
            f"{current['overall']} baseline={current['baseline']} "
            f"runs={current['multiview_run']} views={current['view_calls']} "
            f"switches={current['switches']}"
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
    summary = summarize_cascade_integrated_records(records, audit_labels=audit_labels)
    summary["rule"] = effective_rule_name(args.trigger_policy)
    if summary.get("posthoc_audit_summary"):
        summary["posthoc_audit_summary"]["variant"] = summary["rule"]
    summary.update(
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "boundary": BOUNDARY,
            "split_name": args.split_name,
            "llm_name": args.llm_name,
            "baseline_model_path": args.baseline_model_path,
            "promptnode_model_path": args.promptnode_model_path,
            "output_file": args.output_file,
            "view_configs": DEFAULT_CASCADE_VIEW_CONFIGS,
            "trigger_policy": args.trigger_policy,
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
