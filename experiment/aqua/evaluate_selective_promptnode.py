import argparse
import asyncio
import contextlib
import datetime
import json
import math
import os
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


os.environ["TOKENIZERS_PARALLELISM"] = "false"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AQUA_DIR = os.path.dirname(__file__)
for path in (REPO_ROOT, AQUA_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from datasets.aqua_dataset import aqua_data_process, aqua_get_predict  # noqa: E402
from experiment.aqua.aqua_prompt_set import ROLE_DESCRIPTION  # noqa: E402
from experiment.aqua.evaluate_aqua import (  # noqa: E402
    apply_prompt_node_policy_to_graph,
    assert_llm_environment_ready,
    assert_valid_evaluation_run,
    describe_agent_outputs,
    describe_candidate_graphs,
    describe_graph,
    resolve_decision_exposure_policy,
)
from experiment.aqua.finetune_aqua import setup_environment  # noqa: E402
from experiment.aqua.prompt_node_graph import select_prompt_node_candidate_graph  # noqa: E402
from experiment.aqua.selective_promptnode_activation import (  # noqa: E402
    RULE_NAME,
    extract_direct_votes,
    should_activate_promptnode,
    summarize_direct_votes,
    write_json,
    write_jsonl,
)
from experiment.utils import convert_to_pyg_graph, generate_graph, load_model  # noqa: E402
from mas_framework.graph.graph import TestGraph  # noqa: E402
from mas_framework.tools.reader.readers import JSONLReader  # noqa: E402
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens  # noqa: E402

import mas_framework.prompt.AQuA_prompt_set  # noqa: E402,F401


INTEGRATED_RULE_NAME = "r062_integrated_selective_promptnode"


def baseline_prefilter_passes(
    baseline_record: Dict[str, Any],
    min_distinct_options: int = 2,
    direct_majority_threshold: int = 2,
) -> Tuple[bool, Dict[str, Any]]:
    direct_summary = summarize_direct_votes(extract_direct_votes(baseline_record))
    block_reason = ""
    if direct_summary["direct_distinct_count"] < min_distinct_options:
        block_reason = "direct_not_conflicted"
    elif direct_summary["direct_max_count"] >= direct_majority_threshold:
        block_reason = "direct_majority"
    features = {
        "rule": INTEGRATED_RULE_NAME,
        **direct_summary,
        "prefilter_passed": block_reason == "",
        "prefilter_block_reason": block_reason,
    }
    return block_reason == "", features


def build_selected_record(
    task: Dict[str, Any],
    baseline_record: Dict[str, Any],
    promptnode_record: Optional[Dict[str, Any]],
    promptnode_was_run: bool,
    gate_features: Dict[str, Any],
    selected_source: str,
) -> Dict[str, Any]:
    true_answer = baseline_record.get("true_answer") or task.get("answer")
    promptnode_prediction = (
        promptnode_record.get("predicted_answer") if promptnode_record is not None else None
    )
    selected_prediction = (
        promptnode_prediction
        if selected_source == "promptnode"
        else baseline_record.get("predicted_answer")
    )

    return {
        "task_id": task.get("task_id") or baseline_record.get("task_id"),
        "question": baseline_record.get("question") or task.get("task"),
        "true_answer": true_answer,
        "predicted_answer": selected_prediction,
        "raw_response": (
            promptnode_record.get("raw_response")
            if selected_source == "promptnode" and promptnode_record is not None
            else baseline_record.get("raw_response")
        ),
        "is_solved": selected_prediction == true_answer,
        "selected_source": selected_source,
        "selection_rule": INTEGRATED_RULE_NAME,
        "replay_gate_rule": RULE_NAME,
        "promptnode_was_run": promptnode_was_run,
        "baseline_prediction": baseline_record.get("predicted_answer"),
        "promptnode_prediction": promptnode_prediction,
        "baseline_is_solved": baseline_record.get("predicted_answer") == true_answer,
        "promptnode_is_solved": promptnode_prediction == true_answer,
        "gate_features": gate_features,
        "baseline_record": baseline_record,
        "promptnode_record": promptnode_record,
    }


def run_task_selective(
    task: Dict[str, Any],
    baseline_runner: Callable[[Dict[str, Any]], Dict[str, Any]],
    promptnode_runner: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    baseline_record = baseline_runner(task)
    prefilter_passed, prefilter_features = baseline_prefilter_passes(baseline_record)
    if not prefilter_passed:
        gate_features = {
            **prefilter_features,
            "activate_promptnode": False,
            "block_reason": prefilter_features["prefilter_block_reason"],
        }
        return build_selected_record(
            task,
            baseline_record,
            None,
            promptnode_was_run=False,
            gate_features=gate_features,
            selected_source="baseline",
        )

    promptnode_record = promptnode_runner(task)
    activate, gate_features = should_activate_promptnode(baseline_record, promptnode_record)
    gate_features = {
        **prefilter_features,
        **gate_features,
        "prefilter_passed": True,
        "prefilter_block_reason": "",
    }
    selected_source = "promptnode" if activate else "baseline"
    return build_selected_record(
        task,
        baseline_record,
        promptnode_record,
        promptnode_was_run=True,
        gate_features=gate_features,
        selected_source=selected_source,
    )


def summarize_integrated_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    solved = sum(1 for record in records if record.get("is_solved"))
    baseline_solved = sum(1 for record in records if record.get("baseline_is_solved"))
    promptnode_solved = sum(1 for record in records if record.get("promptnode_is_solved"))
    promptnode_run_count = sum(1 for record in records if record.get("promptnode_was_run"))
    promptnode_switches = [record for record in records if record.get("selected_source") == "promptnode"]
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
    return {
        "rule": INTEGRATED_RULE_NAME,
        "total_tasks": total,
        "solved_tasks": solved,
        "pass_at_1": solved / total * 100 if total else 0.0,
        "baseline_solved_tasks": baseline_solved,
        "baseline_pass_at_1": baseline_solved / total * 100 if total else 0.0,
        "promptnode_solved_tasks_among_all_tasks": promptnode_solved,
        "promptnode_run_count": promptnode_run_count,
        "promptnode_switch_count": len(promptnode_switches),
        "promptnode_run_rate": promptnode_run_count / total if total else 0.0,
        "delta_vs_baseline": solved - baseline_solved,
        "fixes_vs_baseline": len(fixes),
        "harms_vs_baseline": len(harms),
        "promptnode_run_tasks": [
            record["task_id"] for record in records if record.get("promptnode_was_run")
        ],
        "switch_tasks": [record["task_id"] for record in promptnode_switches],
        "fix_tasks": [record["task_id"] for record in fixes],
        "harm_tasks": [record["task_id"] for record in harms],
    }


def _safe_record_projection(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: record.get(key)
        for key in (
            "task_id",
            "question",
            "true_answer",
            "predicted_answer",
            "raw_response",
            "is_solved",
            "error",
            "num_nodes",
            "num_edges",
            "generated_graph",
            "selected_candidate_index",
            "candidate_graphs",
            "agent_outputs",
        )
        if key in record
    }


async def run_graph_record(
    task: Dict[str, Any],
    model,
    sentence_model: SentenceTransformer,
    role_constraints_dict: Dict[str, str],
    graph_index: int,
    llm_name: str,
    decision_method: str,
    prompt_node_policy: str,
    prompt_node_topology_policy: str,
    decision_exposure_policy: str,
    num_candidate_graphs: int = 1,
) -> Dict[str, Any]:
    task_text = task["task"]
    true_answer = task["answer"]
    task_id = task["task_id"]

    task_embedding = torch.tensor(
        sentence_model.encode(task_text),
        device=model.args.device,
    ).float()
    generated_graphs = generate_graph(
        model,
        task_embedding,
        role_constraints_dict,
        graph_index,
        num_samples=max(num_candidate_graphs, 1),
        batch_size=1,
    )
    if not generated_graphs:
        raise RuntimeError("Graph generation failed.")

    candidate_graphs = [
        apply_prompt_node_policy_to_graph(
            graph,
            prompt_node_policy,
            prompt_node_topology_policy,
        )
        for graph in generated_graphs
    ]
    generated_graph, scored_candidates = select_prompt_node_candidate_graph(candidate_graphs)
    selected_candidate_index = next(
        item["candidate_index"]
        for item in scored_candidates
        if candidate_graphs[item["candidate_index"]] is generated_graph
    )
    pyg_data = convert_to_pyg_graph(generated_graph, task_text)
    pyg_data.prompt_node_policy = prompt_node_policy
    pyg_data.prompt_node_topology_policy = prompt_node_topology_policy
    pyg_data.decision_exposure_policy = resolve_decision_exposure_policy(
        generated_graph,
        decision_exposure_policy,
    )
    test_graph = TestGraph(
        domain="aqua",
        llm_name=llm_name,
        decision_method=decision_method,
        pyg_data=pyg_data,
    )
    result = await test_graph.arun({"task": task_text}, num_rounds=1)
    raw_answer = result[0] if isinstance(result, list) and result else result
    predict_answer = aqua_get_predict(raw_answer)
    candidate_metadata = describe_candidate_graphs(
        candidate_graphs,
        selected_candidate_index,
        scored_candidates,
    )

    return {
        "task_id": task_id,
        "question": task_text,
        "true_answer": true_answer,
        "predicted_answer": predict_answer,
        "raw_response": raw_answer,
        "is_solved": predict_answer == true_answer,
        "num_nodes": generated_graph.number_of_nodes(),
        "num_edges": generated_graph.number_of_edges(),
        "generated_graph": describe_graph(generated_graph),
        "selected_candidate_index": candidate_metadata["selected_candidate_index"],
        "candidate_graphs": candidate_metadata["candidate_graphs"],
        "agent_outputs": describe_agent_outputs(test_graph),
    }


async def run_task_selective_async(
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
        num_candidate_graphs=args.num_candidate_graphs,
    )

    prefilter_passed, prefilter_features = baseline_prefilter_passes(baseline_record)
    if not prefilter_passed:
        gate_features = {
            **prefilter_features,
            "activate_promptnode": False,
            "block_reason": prefilter_features["prefilter_block_reason"],
        }
        return build_selected_record(
            task,
            baseline_record,
            None,
            promptnode_was_run=False,
            gate_features=gate_features,
            selected_source="baseline",
        )

    promptnode_record = await run_graph_record(
        task,
        promptnode_model,
        sentence_model,
        role_constraints_dict,
        graph_index,
        llm_name=args.llm_name,
        decision_method=args.promptnode_decision_method,
        prompt_node_policy="none",
        prompt_node_topology_policy=args.prompt_node_topology_policy,
        decision_exposure_policy=args.promptnode_decision_exposure_policy,
        num_candidate_graphs=args.num_candidate_graphs,
    )

    activate, gate_features = should_activate_promptnode(baseline_record, promptnode_record)
    gate_features = {
        **prefilter_features,
        **gate_features,
        "prefilter_passed": True,
        "prefilter_block_reason": "",
    }
    return build_selected_record(
        task,
        baseline_record,
        promptnode_record,
        promptnode_was_run=True,
        gate_features=gate_features,
        selected_source="promptnode" if activate else "baseline",
    )


def load_aqua_tasks(dataset_path: str, task_split_path: str, limit: Optional[int]) -> List[Dict[str, Any]]:
    full_dataset_raw = JSONLReader.parse_file(dataset_path)
    full_dataset = aqua_data_process(full_dataset_raw)
    with open(task_split_path, encoding="utf-8") as f:
        task_split = json.load(f)
    test_indices = task_split.get("test_indices")
    if not test_indices:
        raise ValueError("Task split file does not contain 'test_indices'.")
    selected_indices = test_indices[:limit] if limit else test_indices
    tasks = []
    for local_idx, dataset_idx in enumerate(selected_indices):
        record = dict(full_dataset[dataset_idx])
        record["task_id"] = f"task_{dataset_idx}"
        record["dataset_index"] = dataset_idx
        record["graph_index"] = local_idx
        tasks.append(record)
    return tasks


def render_integrated_report(summary: Dict[str, Any], records: List[Dict[str, Any]]) -> str:
    switch_lines = []
    for record in records:
        if record.get("selected_source") != "promptnode":
            continue
        gate = record.get("gate_features", {})
        switch_lines.append(
            "| {task_id} | {base} | {pn} | {selected} | {router} | {binding} | {solved} |".format(
                task_id=record.get("task_id"),
                base=record.get("baseline_prediction"),
                pn=record.get("promptnode_prediction"),
                selected=record.get("predicted_answer"),
                router=gate.get("router_option"),
                binding=gate.get("router_binding_status"),
                solved=record.get("is_solved"),
            )
        )
    if not switch_lines:
        switch_lines.append("| none | - | - | - | - | - | - |")

    return "\n".join(
        [
            f"# R062 Integrated Selective PromptNode Report: {summary.get('split_name')}",
            "",
            "## Boundary",
            "",
            "This is a fresh integrated run. The evaluator executes ARG first and runs PromptNodes only when the direct-vote prefilter passes.",
            "The gate does not read `true_answer`, `is_solved`, task ids, or clean/noisy labels.",
            "",
            "## Summary",
            "",
            f"- Selected accuracy: `{summary['solved_tasks']}/{summary['total_tasks']}` = `{summary['pass_at_1']:.2f}%`",
            f"- ARG baseline inside R062: `{summary['baseline_solved_tasks']}/{summary['total_tasks']}` = `{summary['baseline_pass_at_1']:.2f}%`",
            f"- Delta vs baseline: `{summary['delta_vs_baseline']}`",
            f"- PromptNode runs: `{summary['promptnode_run_count']}/{summary['total_tasks']}`",
            f"- PromptNode switches: `{summary['promptnode_switch_count']}`",
            f"- Fix/harm vs baseline: `{summary['fixes_vs_baseline']}/{summary['harms_vs_baseline']}`",
            f"- Cost: `${summary.get('cost', 0.0):.6f}`",
            "",
            "## Switches",
            "",
            "| task_id | baseline | promptnode | selected | router | binding | solved |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *switch_lines,
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fresh integrated selective PromptNode evaluator for AQuA."
    )
    parser.add_argument("--baseline-model-path", required=True)
    parser.add_argument("--promptnode-model-path", required=True)
    parser.add_argument("--dataset-path", default="datasets/AQuA/AQuA.jsonl")
    parser.add_argument("--task-split-path", default="experiment/aqua/task_split_aqua_tail34.json")
    parser.add_argument("--split-name", default="tail34")
    parser.add_argument("--llm-name", default="gpt-4o-2024-08-06")
    parser.add_argument("--baseline-decision-method", default="FinalRefer")
    parser.add_argument("--promptnode-decision-method", default="RouterContractFinalRefer")
    parser.add_argument("--prompt-node-topology-policy", default="canonicalize_generated")
    parser.add_argument("--promptnode-decision-exposure-policy", default="auto")
    parser.add_argument("--num-candidate-graphs", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--summary-log-file", default=None)
    parser.add_argument("--report-md", required=True)
    return parser


def _absolute_from_repo(path: Optional[str], repo_root: str) -> Optional[str]:
    if path is None:
        return None
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(repo_root, path))


def prepare_runtime_paths(
    args: argparse.Namespace,
    repo_root: str = REPO_ROOT,
    aqua_dir: str = AQUA_DIR,
) -> argparse.Namespace:
    for attr in (
        "baseline_model_path",
        "promptnode_model_path",
        "dataset_path",
        "task_split_path",
        "output_file",
        "summary_json",
        "summary_log_file",
        "report_md",
    ):
        setattr(args, attr, _absolute_from_repo(getattr(args, attr, None), repo_root))
    args.runtime_cwd = aqua_dir
    return args


@contextlib.contextmanager
def pushd(path: str):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def infer_model_workdir(
    model_path: str,
    repo_root: str = REPO_ROOT,
    aqua_dir: str = AQUA_DIR,
) -> str:
    config_path = os.path.join(model_path, "configuration.txt")
    if not os.path.exists(config_path):
        return repo_root
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    data_dir = config.get("data_dir")
    if not data_dir or os.path.isabs(str(data_dir)):
        return repo_root
    if os.path.exists(os.path.join(repo_root, data_dir)):
        return repo_root
    if os.path.exists(os.path.join(aqua_dir, data_dir)):
        return aqua_dir
    return repo_root


def load_model_with_workdir(model_path: str, ef: bool = True):
    workdir = infer_model_workdir(model_path)
    with pushd(workdir):
        return load_model(model_path, ef=ef)


async def main_async() -> None:
    args = build_arg_parser().parse_args()
    prepare_runtime_paths(args)
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
    print(f"Loaded {len(tasks)} AQuA tasks for integrated selective evaluation.")

    records: List[Dict[str, Any]] = []
    pbar = tqdm(enumerate(tasks), total=len(tasks), desc="Integrated selective eval")
    for graph_index, task in pbar:
        try:
            record = await run_task_selective_async(
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
                "promptnode_was_run": False,
                "baseline_prediction": None,
                "promptnode_prediction": None,
                "baseline_is_solved": False,
                "promptnode_is_solved": False,
                "gate_features": {},
                "error": str(exc),
            }
        records.append(record)
        write_jsonl(args.output_file, records)
        summary_so_far = summarize_integrated_records(records)
        pbar.set_postfix(
            {
                "Accuracy": f"{summary_so_far['pass_at_1']:.2f}% ({summary_so_far['solved_tasks']}/{summary_so_far['total_tasks']})",
                "PN": f"{summary_so_far['promptnode_run_count']}/{summary_so_far['total_tasks']}",
            }
        )

    prompt_tokens = PromptTokens.instance().value
    completion_tokens = CompletionTokens.instance().value
    assert_valid_evaluation_run(
        records,
        total_tasks=len(tasks),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    summary = summarize_integrated_records(records)
    summary.update(
        {
            "timestamp": datetime.datetime.now().isoformat(),
            "split_name": args.split_name,
            "llm_name": args.llm_name,
            "baseline_model_path": args.baseline_model_path,
            "promptnode_model_path": args.promptnode_model_path,
            "output_file": args.output_file,
            "cost": Cost.instance().value,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "boundary": "fresh_integrated_selective_promptnode_run",
        }
    )
    write_json(args.summary_json, summary)
    with open(args.report_md, "w", encoding="utf-8") as f:
        f.write(render_integrated_report(summary, records))
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
