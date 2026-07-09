import os
import json
import torch
import argparse
import asyncio
from tqdm import tqdm
import sys
import datetime

os.environ["TOKENIZERS_PARALLELISM"] = "false"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from mas_framework.utils.globals import Cost, PromptTokens, CompletionTokens

from sentence_transformers import SentenceTransformer
from mas_framework.tools.reader.readers import JSONLReader
from mas_framework.graph.graph import TestGraph
from experiment.utils import load_model, generate_graph, convert_to_pyg_graph
from experiment.aqua.prompt_node_graph import (
    augment_graph_with_prompt_nodes,
    canonicalize_prompt_node_topology,
    select_prompt_node_candidate_graph,
)
from experiment.aqua.tail34_template_candidate_materialize import (
    candidate_record_to_networkx,
)
from datasets.aqua_dataset import aqua_data_process, aqua_get_predict
try:
    from experiment.aqua.finetune_aqua import setup_environment
    from experiment.aqua.aqua_prompt_set import ROLE_DESCRIPTION
except ImportError:
    from finetune_aqua import setup_environment
    from aqua_prompt_set import ROLE_DESCRIPTION
import mas_framework.prompt.AQuA_prompt_set

INFRASTRUCTURE_ERROR_MARKERS = (
    "RetryError",
    "Missing API_KEY",
    "OPENAI_API_KEY",
    "insufficient_quota",
    "RateLimitError",
    "APIConnectionError",
    "APIStatusError",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate model on Aqua")
    parser.add_argument('--model_path', type=str,
                        default='output/xxxx',
                        help="Path to trained model directory")
    parser.add_argument('--dataset_path', type=str, default='../../datasets/AQuA/AQuA.jsonl')
    parser.add_argument('--task_split_path', type=str, default='./task_split_aqua.json')
    parser.add_argument('--llm_name', type=str, default="gpt-4o-2024-08-06")
    parser.add_argument('--decision_method', type=str, default="FinalRefer")
    parser.add_argument('--output_file', type=str, default='aqua_eval_results.jsonl')
    parser.add_argument('--summary_log_file', type=str, default='./res_logs/evaluation_summary.jsonl')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--eval_batch_size', type=int, default=10)
    parser.add_argument('--prompt_node_policy', type=str, default='none',
                        choices=['none', 'memory_verifier', 'memory_verifier_router'])
    parser.add_argument('--prompt_node_topology_policy', type=str, default='none',
                        choices=['none', 'canonicalize_generated', 'canonicalize_or_insert'])
    parser.add_argument('--decision_exposure_policy', type=str, default='auto',
                        choices=['auto', 'all', 'terminal'])
    parser.add_argument('--num_candidate_graphs', type=int, default=1)
    parser.add_argument('--forced_template_candidate_jsonl', type=str, default=None,
                        help="Optional R083-style JSONL candidate pool. When set, evaluate the selected template graph instead of sampling ARG-Designer.")
    parser.add_argument('--forced_template_candidate_rank', type=int, default=1,
                        help="1-based candidate rank to execute from --forced_template_candidate_jsonl.")
    return parser.parse_args()


def assert_llm_environment_ready(llm_name):
    if not str(llm_name or "").startswith("gpt"):
        return
    if (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip():
        return
    raise RuntimeError(
        "Missing API_KEY or OPENAI_API_KEY before starting GPT evaluation. "
        "Load a valid .env or export an API key before running evaluate_aqua.py."
    )


def apply_prompt_node_policy_to_graph(
    nx_graph, prompt_node_policy='none', prompt_node_topology_policy='none'
):
    if prompt_node_policy in (None, 'none'):
        graph = nx_graph
    else:
        graph = augment_graph_with_prompt_nodes(nx_graph, policy=prompt_node_policy)
    return canonicalize_prompt_node_topology(
        graph, policy=prompt_node_topology_policy
    )


def resolve_decision_exposure_policy(nx_graph, requested_policy='auto'):
    if requested_policy in (None, 'auto'):
        return "terminal" if nx_graph.graph.get("canonicalized_prompt_nodes") else "all"
    return requested_policy

def describe_graph(nx_graph):
    return {
        "roles": [nx_graph.nodes[n].get("role", "Unknown") for n in nx_graph.nodes()],
        "edges": [[int(u), int(v)] for u, v in nx_graph.edges()],
    }

def describe_candidate_graphs(candidate_graphs, selected_index, scored_candidates):
    described = []
    scored_by_idx = {item["candidate_index"]: item for item in scored_candidates}
    for idx, graph in enumerate(candidate_graphs):
        record = describe_graph(graph)
        record.update(scored_by_idx.get(idx, {}))
        described.append(record)
    return {
        "selected_candidate_index": selected_index,
        "candidate_graphs": described,
    }

def describe_agent_outputs(test_graph):
    node_list = list(test_graph.nodes.values())
    node_to_idx = {node.id: idx for idx, node in enumerate(node_list)}
    outputs = []
    for idx, node in enumerate(node_list):
        outputs.append({
            "node": idx,
            "role": node.role,
            "predecessors": [node_to_idx[p.id] for p in node.spatial_predecessors if p.id in node_to_idx],
            "outputs": node.outputs,
        })
    return outputs


def load_forced_template_candidate_pool(path):
    pool = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            task_id = record.get("task_id")
            if not task_id:
                raise ValueError(f"Forced template candidate row is missing task_id: {path}")
            pool[task_id] = record
    return pool


def select_forced_template_candidate_graph(candidate_pool, task_id, rank=1):
    if task_id not in candidate_pool:
        raise KeyError(f"No forced template candidates found for {task_id}")
    row = candidate_pool[task_id]
    candidates = list(row.get("candidates") or [])
    if not candidates:
        raise ValueError(f"Forced template candidate row has no candidates: {task_id}")
    if rank < 1 or rank > len(candidates):
        raise ValueError(f"Candidate rank {rank} out of range for {task_id}; available={len(candidates)}")
    candidate_graphs = [candidate_record_to_networkx(candidate) for candidate in candidates]
    selected_index = rank - 1
    selected_graph = candidate_graphs[selected_index]
    selected_graph.graph["selected_candidate_rank"] = rank
    selected_graph.graph["forced_template_task_id"] = task_id
    return selected_graph, candidate_graphs, selected_index


def _is_infrastructure_error_record(record):
    error = str(record.get("error", ""))
    return bool(error) and any(marker in error for marker in INFRASTRUCTURE_ERROR_MARKERS)


def _has_model_response(record):
    return bool(record.get("raw_response")) or bool(record.get("predicted_answer"))


def assert_valid_evaluation_run(records, total_tasks, prompt_tokens, completion_tokens):
    """Reject runs where every task failed before any LLM response was billed."""
    if total_tasks <= 0 or len(records) < total_tasks:
        return
    if prompt_tokens or completion_tokens:
        return
    if not records:
        return
    if all(_is_infrastructure_error_record(record) and not _has_model_response(record) for record in records):
        raise RuntimeError(
            "No successful LLM calls were recorded: all evaluation records are infrastructure "
            "errors and prompt/completion token counts are zero. Do not treat this run as an "
            "accuracy result; check API_KEY/OPENAI_API_KEY, BASE_URL, model access, and quota."
        )


async def main(ef=True):
    args = parse_args()
    assert_llm_environment_ready(args.llm_name)
    setup_environment(42)

    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    forced_template_pool = None
    if args.forced_template_candidate_jsonl:
        forced_template_pool = load_forced_template_candidate_pool(args.forced_template_candidate_jsonl)
        args.model_name = f"forced_template_rank{args.forced_template_candidate_rank}"
        simple_ar_model = None
        sentence_model = None
        print(
            "Using forced template candidate pool: "
            f"{args.forced_template_candidate_jsonl} rank={args.forced_template_candidate_rank}"
        )
    else:
        print("Loading model and tools...")
        simple_ar_model = load_model(args.model_path, ef=ef)
        if ef:
            args.model_name = 'ef_best'
        else:
            args.model_name = 'best'
        simple_ar_model.eval()
        sentence_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    role_constraints_dict = ROLE_DESCRIPTION

    full_dataset_raw = JSONLReader.parse_file(args.dataset_path)
    full_dataset = aqua_data_process(full_dataset_raw)

    if not os.path.exists(args.task_split_path):
        raise FileNotFoundError(f"Task split file '{args.task_split_path}' not found. Run cold_start_aqua.py first.")
    with open(args.task_split_path, 'r') as f:
        task_split = json.load(f)
    test_indices = task_split.get('test_indices')
    if not test_indices:
        raise ValueError("Task split file does not contain 'test_indices'.")

    dataset = [full_dataset[i] for i in test_indices]

    if args.limit:
        dataset = dataset[:args.limit]
    print(f"Loaded {len(dataset)} Aqua test samples for evaluation.")

    total_tasks = len(dataset)
    solved_tasks = 0
    results_list = []

    from typing import Iterator, List, Any
    import math

    def eval_loader(data: List[Any], batch_size: int) -> Iterator[List[Any]]:
        records = []
        for record in data:
            records.append(record)
            if len(records) >= batch_size:
                yield records
                records = []
        if records:
            yield records
    
    num_batches = math.ceil(total_tasks / args.eval_batch_size)

    pbar = tqdm(enumerate(eval_loader(dataset, args.eval_batch_size)), total=num_batches, desc="Evaluating model")
    for i_batch, record_batch in pbar:
        answer_tasks = []
        metadata_for_tasks = []

        for i_record, record in enumerate(record_batch):
            task_text = record["task"]
            true_answer = record["answer"]
            global_idx = i_batch * args.eval_batch_size + i_record
            task_id = f"task_{test_indices[global_idx]}"

            try:
                if forced_template_pool is not None:
                    generated_graph, candidate_graphs, selected_candidate_index = (
                        select_forced_template_candidate_graph(
                            forced_template_pool,
                            task_id,
                            rank=args.forced_template_candidate_rank,
                        )
                    )
                    scored_candidates = [
                        {
                            "candidate_index": index,
                            "rank": graph.graph.get("selected_candidate_rank"),
                            "support_count": graph.graph.get("support_count"),
                            "graph_signature": graph.graph.get("graph_signature"),
                            "forced_template_candidate": True,
                        }
                        for index, graph in enumerate(candidate_graphs)
                    ]
                else:
                    task_embedding = torch.tensor(sentence_model.encode(task_text),
                                                  device=simple_ar_model.args.device).float()
                    generated_graphs = generate_graph(
                        simple_ar_model,
                        task_embedding,
                        role_constraints_dict,
                        global_idx,
                        num_samples=max(args.num_candidate_graphs, 1),
                        batch_size=1,
                    )

                    if not generated_graphs:
                        raise RuntimeError("Graph generation failed.")

                    candidate_graphs = [
                        apply_prompt_node_policy_to_graph(
                            graph,
                            args.prompt_node_policy,
                            args.prompt_node_topology_policy,
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
                pyg_data.prompt_node_policy = (
                    "forced_template"
                    if forced_template_pool is not None
                    else args.prompt_node_policy
                )
                pyg_data.prompt_node_topology_policy = (
                    generated_graph.graph.get("prompt_node_topology_policy", "clean_fix_template")
                    if forced_template_pool is not None
                    else args.prompt_node_topology_policy
                )
                pyg_data.decision_exposure_policy = resolve_decision_exposure_policy(
                    generated_graph, args.decision_exposure_policy
                )
                test_graph = TestGraph(domain="aqua", llm_name=args.llm_name,
                                       decision_method=args.decision_method, pyg_data=pyg_data)

                coro = test_graph.arun({"task": task_text}, num_rounds=1)
                answer_tasks.append(coro)
                metadata_for_tasks.append({
                    "task_id": task_id, "task_text": task_text, "true_answer": true_answer,
                    "generated_graph": generated_graph,
                    "test_graph": test_graph,
                    "candidate_graphs": candidate_graphs,
                    "selected_candidate_index": selected_candidate_index,
                    "scored_candidates": scored_candidates,
                })

            except Exception as e:
                print(f"Error preparing task {task_id}: {e}")
                results_list.append({
                    "task_id": task_id, "question": task_text, "true_answer": true_answer,
                    "predicted_answer": None, "raw_response": None, "is_solved": False, "error": str(e)
                })

        if not answer_tasks:
            continue
        
        all_results = await asyncio.gather(*answer_tasks, return_exceptions=True)

        for i, result in enumerate(all_results):
            metadata = metadata_for_tasks[i]
            task_id = metadata["task_id"]
            task_text = metadata["task_text"]
            true_answer = metadata["true_answer"]
            generated_graph = metadata["generated_graph"]
            test_graph = metadata["test_graph"]
            candidate_metadata = describe_candidate_graphs(
                metadata.get("candidate_graphs", [generated_graph]),
                metadata.get("selected_candidate_index", 0),
                metadata.get("scored_candidates", []),
            )
            
            if isinstance(result, Exception):
                print(f"Error executing task {task_id}: {result}")
                results_list.append({
                    "task_id": task_id, "question": task_text, "true_answer": true_answer,
                    "predicted_answer": None, "raw_response": None, "is_solved": False, "error": str(result)
                })
                continue
                
            raw_answer = result
            raw_answer = raw_answer[0] if isinstance(raw_answer, list) and raw_answer else raw_answer

            predict_answer = aqua_get_predict(raw_answer)
            is_solved = predict_answer == true_answer

            if is_solved:
                solved_tasks += 1
            
            results_list.append({
                "task_id": task_id, "question": task_text, "true_answer": true_answer,
                "predicted_answer": predict_answer, "raw_response": raw_answer, "is_solved": is_solved,
                "num_nodes": generated_graph.number_of_nodes(), "num_edges": generated_graph.number_of_edges(),
                "generated_graph": describe_graph(generated_graph),
                "selected_candidate_index": candidate_metadata["selected_candidate_index"],
                "candidate_graphs": candidate_metadata["candidate_graphs"],
                "agent_outputs": describe_agent_outputs(test_graph),
            })

        current_processed = len(results_list)
        acc = solved_tasks / current_processed * 100 if current_processed > 0 else 0
        pbar.set_postfix({
            "Accuracy": f"{acc:.2f}% ({solved_tasks}/{current_processed})",
            "Token": f"${PromptTokens.instance().value:.4f}",
        })
        
        with open(args.output_file, 'w', encoding='utf-8') as f:
            for res in results_list:
                f.write(json.dumps(res) + '\n')

    pass_at_1 = (solved_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    final_cost = Cost.instance().value
    final_prompt_tokens = PromptTokens.instance().value
    final_completion_tokens = CompletionTokens.instance().value
    assert_valid_evaluation_run(
        results_list,
        total_tasks=total_tasks,
        prompt_tokens=final_prompt_tokens,
        completion_tokens=final_completion_tokens,
    )

    print("\n" + "=" * 50 + "\nEvaluation Summary")
    print(f"Model path: {args.model_path}")
    print(f"Total tasks: {total_tasks}, Solved: {solved_tasks}, Pass@1: {pass_at_1:.2f}%")
    print("-" * 50)
    print(f"Total cost: ${final_cost:.6f}")
    print(f"Total Prompt Tokens: {int(final_prompt_tokens)}")
    print(f"Total Completion Tokens: {int(final_completion_tokens)}")
    print("-" * 50)
    print(f"Detailed results saved to: {args.output_file}")

    log_record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "dataset": "aqua",
        "model_path": args.model_path+args.model_name,
        "llm_name": args.llm_name,
        "total_tasks": total_tasks,
        "solved_tasks": solved_tasks,
        "pass_at_1": pass_at_1,
        "cost": final_cost,
        "prompt_tokens": final_prompt_tokens,
        "completion_tokens": final_completion_tokens,
        "detail_file": args.output_file
    }

    try:
        os.makedirs(os.path.dirname(args.summary_log_file), exist_ok=True)
        with open(args.summary_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_record) + '\n')
        print(f"Summary appended to: {args.summary_log_file}")
    except Exception as e:
        print(f"Failed to write summary log file: {e}")
    print("=" * 50)


if __name__ == '__main__':
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(True))
