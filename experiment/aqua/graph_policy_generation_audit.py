import argparse
import json
import os
import random
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List

import networkx as nx
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.aqua_adapter import AquaGraphDataset  # noqa: E402
from experiment.utils import load_model  # noqa: E402


PN_ROLES = {"PN_Memory", "PN_Verifier", "PN_Router"}


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def promptnode_count(graph: nx.Graph) -> int:
    return sum(1 for _, data in graph.nodes(data=True) if data.get("role") in PN_ROLES)


def summarize_generated_graphs(graphs: Iterable[nx.Graph]) -> Dict[str, Any]:
    graph_list = list(graphs)
    role_counts: Counter[str] = Counter()
    node_counts: List[int] = []
    edge_counts: List[int] = []
    promptnode_nodes = 0
    promptnode_graphs = 0
    dag_graphs = 0

    for graph in graph_list:
        node_counts.append(graph.number_of_nodes())
        edge_counts.append(graph.number_of_edges())
        pn_count = promptnode_count(graph)
        promptnode_nodes += pn_count
        if pn_count:
            promptnode_graphs += 1
        if nx.is_directed_acyclic_graph(graph):
            dag_graphs += 1
        for _, data in graph.nodes(data=True):
            role_counts[data.get("role", "Unknown")] += 1

    sampled_graphs = len(graph_list)
    return {
        "sampled_graphs": sampled_graphs,
        "promptnode_graphs": promptnode_graphs,
        "promptnode_nodes": promptnode_nodes,
        "promptnode_graph_rate": promptnode_graphs / sampled_graphs if sampled_graphs else 0.0,
        "avg_promptnode_nodes": promptnode_nodes / sampled_graphs if sampled_graphs else 0.0,
        "dag_graphs": dag_graphs,
        "dag_rate": dag_graphs / sampled_graphs if sampled_graphs else 0.0,
        "min_nodes": min(node_counts) if node_counts else 0,
        "max_nodes": max(node_counts) if node_counts else 0,
        "avg_nodes": sum(node_counts) / sampled_graphs if sampled_graphs else 0.0,
        "min_edges": min(edge_counts) if edge_counts else 0,
        "max_edges": max(edge_counts) if edge_counts else 0,
        "avg_edges": sum(edge_counts) / sampled_graphs if sampled_graphs else 0.0,
        "role_counts": dict(sorted(role_counts.items())),
    }


def _graph_task_embedding(graph: nx.Graph, device: torch.device) -> torch.Tensor:
    embedding = graph.graph.get("task_embedding")
    if embedding is None:
        raise ValueError("Finetune graph missing task_embedding")
    if isinstance(embedding, torch.Tensor):
        return embedding.to(device).float()
    return torch.tensor(embedding, device=device).float()


def audit_generation(
    model_dir: str,
    finetune_data_dir: str,
    sample_tasks: int,
    samples_per_task: int,
    batch_size: int,
    seed: int,
    ef: bool = True,
) -> Dict[str, Any]:
    random.seed(seed)
    torch.manual_seed(seed)

    model = load_model(model_dir, ef=ef)
    dataset = AquaGraphDataset(
        data_dir="experiment/ColdStartData_Aqua",
        data_dir_ef=finetune_data_dir,
        sample_size=sample_tasks,
        pretrain=False,
    )
    if not dataset.graph_list:
        raise ValueError(f"No finetune graphs found in {finetune_data_dir}")

    generated_graphs: List[nx.Graph] = []
    task_records: List[Dict[str, Any]] = []
    with torch.no_grad():
        for task_index, source_graph in enumerate(dataset.graph_list):
            task_embedding = _graph_task_embedding(source_graph, model.args.device)
            task_graphs: List[nx.Graph] = []
            remaining = samples_per_task
            while remaining > 0:
                current_batch = min(batch_size, remaining)
                batch_graphs = model.sample(
                    num_samples=current_batch,
                    batch_size=current_batch,
                    task_embedding=task_embedding,
                )
                task_graphs.extend(batch_graphs)
                generated_graphs.extend(batch_graphs)
                remaining -= current_batch
            task_records.append(
                {
                    "task_index": task_index,
                    "sampled_graphs": len(task_graphs),
                    "promptnode_graphs": sum(1 for graph in task_graphs if promptnode_count(graph) > 0),
                    "promptnode_nodes": sum(promptnode_count(graph) for graph in task_graphs),
                }
            )

    summary = summarize_generated_graphs(generated_graphs)
    summary.update(
        {
            "model_dir": model_dir,
            "model_file": "ef_best_model.pth" if ef else "best_model.pth",
            "finetune_data_dir": finetune_data_dir,
            "sample_tasks": len(dataset.graph_list),
            "samples_per_task": samples_per_task,
            "batch_size": batch_size,
            "seed": seed,
            "task_records": task_records,
            "claim_boundary": (
                "Graph-generation audit only. This samples ARGDesigner's graph generator and checks whether "
                "PromptNode roles appear before execution; it does not evaluate AQuA answer accuracy."
            ),
        }
    )
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    role_lines = [
        f"- `{role}`: `{count}`"
        for role, count in sorted(summary["role_counts"].items(), key=lambda item: (-item[1], item[0]))
    ]
    return "\n".join(
        [
            "# R055 PromptNode Graph-Policy Generation Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Model dir: `{summary['model_dir']}`",
            f"- Model file: `{summary['model_file']}`",
            f"- Finetune data: `{summary['finetune_data_dir']}`",
            f"- Sample tasks: `{summary['sample_tasks']}`",
            f"- Samples per task: `{summary['samples_per_task']}`",
            f"- Sampled graphs: `{summary['sampled_graphs']}`",
            f"- PromptNode graphs: `{summary['promptnode_graphs']}`",
            f"- PromptNode graph rate: `{summary['promptnode_graph_rate']:.4f}`",
            f"- PromptNode nodes: `{summary['promptnode_nodes']}`",
            f"- Average PromptNode nodes per graph: `{summary['avg_promptnode_nodes']:.4f}`",
            f"- DAG graphs: `{summary['dag_graphs']}`",
            f"- DAG rate: `{summary['dag_rate']:.4f}`",
            f"- Node range: `{summary['min_nodes']}-{summary['max_nodes']}`",
            f"- Edge range: `{summary['min_edges']}-{summary['max_edges']}`",
            "",
            "## Role Counts",
            "",
            *(role_lines or ["- none"]),
            "",
            "## Interpretation",
            "",
            "This audit checks whether the trained graph generator itself emits PromptNode roles before any MAS "
            "execution or final answer aggregation. A low PromptNode graph rate means the finetune path is valid "
            "but the generator still has not learned the user's intended virtual-node insertion behavior strongly enough.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit PromptNode roles in sampled ARGDesigner graphs.")
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--finetune-data-dir", default="experiment/FinetuneData_AQuA_PN_GraphPolicy_R053")
    parser.add_argument("--sample-tasks", type=int, default=8)
    parser.add_argument("--samples-per-task", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260708)
    parser.add_argument("--best-model", action="store_true", help="Load best_model.pth instead of ef_best_model.pth")
    parser.add_argument("--summary-json", default="experiment/aqua/res_logs/aqua_graph_policy_generation_audit_summary.json")
    parser.add_argument("--report-md", default="experiment/aqua/run_logs/aqua_graph_policy_generation_audit_report.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = audit_generation(
        model_dir=args.model_dir,
        finetune_data_dir=args.finetune_data_dir,
        sample_tasks=args.sample_tasks,
        samples_per_task=args.samples_per_task,
        batch_size=args.batch_size,
        seed=args.seed,
        ef=not args.best_model,
    )
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary))
    print(
        "R055 generation audit: "
        f"sampled={summary['sampled_graphs']} "
        f"pn_graphs={summary['promptnode_graphs']} "
        f"pn_rate={summary['promptnode_graph_rate']:.4f} "
        f"dag_rate={summary['dag_rate']:.4f}"
    )


if __name__ == "__main__":
    main()
