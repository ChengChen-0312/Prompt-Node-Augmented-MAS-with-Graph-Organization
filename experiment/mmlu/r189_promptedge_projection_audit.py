from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List

import networkx as nx
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.mmlu_prompt_set import ROLE_DESCRIPTION
from experiment.mmlu.promptedge_topology import inject_promptedge_topology
from experiment.mmlu.r187_promptedge_generated_graph_audit import (
    audit_generated_graph,
    load_tasks,
)
from experiment.utils import generate_graph, load_model


DEFAULT_MODEL_DIR = "experiment/mmlu/output/mmlu_promptedge_pn_graph_policy_r188_e5"
DEFAULT_TRANSFER_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r189_promptedge_projection_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r189_promptedge_projection_audit_report.md"
DEFAULT_DETAILS_JSONL = "experiment/mmlu/run_logs/mmlu_r189_promptedge_projection_audit_details.jsonl"


def strip_promptnodes(graph: nx.DiGraph) -> nx.DiGraph:
    ordered_nodes = (
        list(nx.topological_sort(graph))
        if nx.is_directed_acyclic_graph(graph)
        else list(graph.nodes())
    )
    non_pn_nodes = [
        node
        for node in ordered_nodes
        if not str(graph.nodes[node].get("role", "")).startswith("PN_")
    ]
    stripped = nx.DiGraph()
    node_map = {old: new for new, old in enumerate(non_pn_nodes)}
    for old, new in node_map.items():
        stripped.add_node(new, **dict(graph.nodes[old]))
    for src, dst in graph.edges():
        if src in node_map and dst in node_map:
            stripped.add_edge(node_map[src], node_map[dst], **dict(graph.edges[src, dst]))
    if stripped.number_of_nodes() == 0:
        stripped.add_node(0, role="Knowlegable Expert", constraint=ROLE_DESCRIPTION["Knowlegable Expert"])
    return stripped


def project_generated_graph_to_promptedge_contract(graph: nx.DiGraph) -> nx.DiGraph:
    base_graph = strip_promptnodes(graph)
    if not nx.is_directed_acyclic_graph(base_graph):
        dag = nx.DiGraph()
        for idx, (_, data) in enumerate(base_graph.nodes(data=True)):
            dag.add_node(idx, **dict(data))
            if idx > 0:
                dag.add_edge(idx - 1, idx)
        base_graph = dag
    return inject_promptedge_topology(base_graph, decision_exposure_policy="terminal")


def run_projection_audit(
    model_dir: str,
    transfer_jsonl: str,
    summary_json: str,
    report_md: str,
    details_jsonl: str,
    num_tasks: int,
    seed: int,
) -> Dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    model = load_model(model_dir, ef=False)
    sentence_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    tasks = load_tasks(transfer_jsonl, num_tasks)
    details: List[Dict[str, Any]] = []

    for idx, task in enumerate(tasks):
        task_embedding = torch.tensor(
            sentence_model.encode(task["question"]),
            device=model.args.device,
        ).float()
        raw_graph = generate_graph(
            model,
            task_embedding,
            ROLE_DESCRIPTION,
            question_id=idx,
            num_samples=1,
            batch_size=1,
        )[0]
        projected_graph = project_generated_graph_to_promptedge_contract(raw_graph)
        raw_audit = audit_generated_graph(raw_graph)
        projected_audit = audit_generated_graph(projected_graph)
        details.append(
            {
                "task_id": task["task_id"],
                "subject": task["subject"],
                "question_used_for_embedding": True,
                "answer_used": False,
                "raw": raw_audit,
                "projected": projected_audit,
                "projection_added_nodes": projected_graph.number_of_nodes() - raw_graph.number_of_nodes(),
                "projection_policy": "strip generated PN nodes; preserve non-PN agent graph; inject canonical PN_Memory->PN_Verifier->PN_Router PromptEdge chain before execution",
            }
        )

    total = len(details)

    def raw_count(key: str) -> int:
        return sum(1 for row in details if row["raw"].get(key))

    def projected_count(key: str) -> int:
        return sum(1 for row in details if row["projected"].get(key))

    summary = {
        "run_id": "R189",
        "title": "MMLU PromptEdge structural projection audit",
        "claim_boundary": (
            "No-API graph projection audit only. This supports a hybrid constrained-decoder "
            "claim, not a fully learned edge-linking claim and not an answer accuracy claim."
        ),
        "no_api": True,
        "broad_api": False,
        "model_dir": model_dir,
        "transfer_jsonl": transfer_jsonl,
        "tasks_audited": total,
        "raw_contract_ready_graphs": raw_count("promptedge_contract_ready"),
        "projected_contract_ready_graphs": projected_count("promptedge_contract_ready"),
        "raw_pn_chain_graphs": raw_count("has_pn_chain"),
        "projected_pn_chain_graphs": projected_count("has_pn_chain"),
        "raw_dag_graphs": raw_count("is_dag"),
        "projected_dag_graphs": projected_count("is_dag"),
        "projection_contract_ready_rate": projected_count("promptedge_contract_ready") / total if total else 0.0,
        "raw_contract_ready_rate": raw_count("promptedge_contract_ready") / total if total else 0.0,
        "projection_audit_pass": total > 0
        and projected_count("is_dag") == total
        and projected_count("promptedge_contract_ready") == total,
        "details_jsonl": details_jsonl,
        "paper_claim_boundary": (
            "May claim structural projection yields execution-ready PromptEdge graphs; "
            "must not claim learned edge policy without an ablation separating raw learned graph from projection."
        ),
        "next_action": "R190 goal audit should decide whether a tiny API smoke is justified under a hybrid constrained-decoder claim.",
    }

    os.makedirs(os.path.dirname(details_jsonl), exist_ok=True)
    with open(details_jsonl, "w", encoding="utf-8") as f:
        for row in details:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))

    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R189 MMLU PromptEdge Projection Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Tasks audited: `{summary['tasks_audited']}`",
            f"- Raw contract-ready graphs: `{summary['raw_contract_ready_graphs']}`",
            f"- Projected contract-ready graphs: `{summary['projected_contract_ready_graphs']}`",
            f"- Raw PN-chain graphs: `{summary['raw_pn_chain_graphs']}`",
            f"- Projected PN-chain graphs: `{summary['projected_pn_chain_graphs']}`",
            f"- Raw DAG graphs: `{summary['raw_dag_graphs']}`",
            f"- Projected DAG graphs: `{summary['projected_dag_graphs']}`",
            f"- Projection audit pass: `{summary['projection_audit_pass']}`",
            "",
            "## Paper Boundary",
            "",
            summary["paper_claim_boundary"],
            "",
            "## Next",
            "",
            summary["next_action"],
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit structural projection for generated MMLU PN/PE graphs.")
    parser.add_argument("--model_dir", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--transfer_jsonl", default=DEFAULT_TRANSFER_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--details_jsonl", default=DEFAULT_DETAILS_JSONL)
    parser.add_argument("--num_tasks", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_projection_audit(
        model_dir=args.model_dir,
        transfer_jsonl=args.transfer_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
        details_jsonl=args.details_jsonl,
        num_tasks=args.num_tasks,
        seed=args.seed,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
