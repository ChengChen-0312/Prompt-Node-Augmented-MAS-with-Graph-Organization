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
from experiment.utils import generate_graph, load_model


DEFAULT_MODEL_DIR = "experiment/mmlu/output/mmlu_promptedge_pn_graph_policy_r186_short"
DEFAULT_TRANSFER_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r187_promptedge_generated_graph_audit_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r187_promptedge_generated_graph_audit_report.md"
DEFAULT_DETAILS_JSONL = "experiment/mmlu/run_logs/mmlu_r187_promptedge_generated_graph_audit_details.jsonl"

PN_ROLES = {"PN_Memory", "PN_Verifier", "PN_Router"}


def audit_generated_graph(graph: nx.DiGraph) -> Dict[str, Any]:
    roles = {node: data.get("role", "") for node, data in graph.nodes(data=True)}
    role_values = list(roles.values())
    role_to_nodes: Dict[str, List[Any]] = {}
    for node, role in roles.items():
        role_to_nodes.setdefault(role, []).append(node)

    def has_role_edge(src_role: str, dst_role: str) -> bool:
        for src in role_to_nodes.get(src_role, []):
            for dst in role_to_nodes.get(dst_role, []):
                if graph.has_edge(src, dst):
                    return True
        return False

    has_pn_chain = has_role_edge("PN_Memory", "PN_Verifier") and has_role_edge(
        "PN_Verifier", "PN_Router"
    )
    router_is_terminal = any(
        graph.out_degree(node) == 0 for node in role_to_nodes.get("PN_Router", [])
    )
    return {
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "roles": role_values,
        "is_dag": nx.is_directed_acyclic_graph(graph),
        "has_any_pn": any(role.startswith("PN_") for role in role_values),
        "has_all_pn_roles": PN_ROLES.issubset(set(role_values)),
        "pn_role_count": sum(1 for role in role_values if role.startswith("PN_")),
        "has_pn_chain": has_pn_chain,
        "router_is_terminal": router_is_terminal,
        "promptedge_contract_ready": nx.is_directed_acyclic_graph(graph)
        and has_pn_chain
        and router_is_terminal,
    }


def load_tasks(path: str, limit: int) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if len(rows) >= limit:
                break
            row = json.loads(line)
            rows.append(
                {
                    "task_id": row.get("task_id", f"task_{len(rows)}"),
                    "question": row.get("task") or row.get("question", ""),
                    "subject": row.get("subject", ""),
                }
            )
    return rows


def run_audit(
    model_dir: str,
    transfer_jsonl: str,
    summary_json: str,
    report_md: str,
    details_jsonl: str,
    num_tasks: int,
    seed: int,
    run_id: str = "R187",
) -> Dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    model = load_model(model_dir, ef=False)
    sentence_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    tasks = load_tasks(transfer_jsonl, num_tasks)
    details = []

    for idx, task in enumerate(tasks):
        task_embedding = torch.tensor(
            sentence_model.encode(task["question"]),
            device=model.args.device,
        ).float()
        generated = generate_graph(
            model,
            task_embedding,
            ROLE_DESCRIPTION,
            question_id=idx,
            num_samples=1,
            batch_size=1,
        )
        graph = generated[0]
        audit = audit_generated_graph(graph)
        details.append(
            {
                "task_id": task["task_id"],
                "subject": task["subject"],
                "question_used_for_embedding": True,
                "answer_used": False,
                **audit,
            }
        )

    def count(key: str) -> int:
        return sum(1 for row in details if row.get(key))

    total = len(details)
    summary = {
        "run_id": run_id,
        "title": "MMLU PN-capable generated graph audit",
        "claim_boundary": (
            "Graph-generation audit only. No API evaluation, no answer labels used, "
            "and no accuracy claim."
        ),
        "no_api": True,
        "broad_api": False,
        "model_dir": model_dir,
        "transfer_jsonl": transfer_jsonl,
        "tasks_audited": total,
        "dag_graphs": count("is_dag"),
        "graphs_with_any_pn": count("has_any_pn"),
        "graphs_with_all_pn_roles": count("has_all_pn_roles"),
        "graphs_with_pn_chain": count("has_pn_chain"),
        "graphs_with_terminal_router": count("router_is_terminal"),
        "promptedge_contract_ready_graphs": count("promptedge_contract_ready"),
        "any_pn_rate": count("has_any_pn") / total if total else 0.0,
        "pn_chain_rate": count("has_pn_chain") / total if total else 0.0,
        "contract_ready_rate": count("promptedge_contract_ready") / total if total else 0.0,
        "mean_nodes": sum(row["num_nodes"] for row in details) / total if total else 0.0,
        "mean_pn_roles": sum(row["pn_role_count"] for row in details) / total if total else 0.0,
        "graph_audit_pass": total > 0
        and count("is_dag") == total
        and count("promptedge_contract_ready") >= max(1, int(0.5 * total)),
        "details_jsonl": details_jsonl,
        "next_action": "Use audit result to decide whether to run more graph-policy training or only a tiny API smoke.",
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
            f"# {summary['run_id']} MMLU Generated Graph Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Tasks audited: `{summary['tasks_audited']}`",
            f"- DAG graphs: `{summary['dag_graphs']}`",
            f"- Graphs with any PN: `{summary['graphs_with_any_pn']}`",
            f"- Graphs with all PN roles: `{summary['graphs_with_all_pn_roles']}`",
            f"- Graphs with PN chain: `{summary['graphs_with_pn_chain']}`",
            f"- Graphs with terminal router: `{summary['graphs_with_terminal_router']}`",
            f"- Contract-ready graphs: `{summary['promptedge_contract_ready_graphs']}`",
            f"- Mean nodes: `{summary['mean_nodes']:.2f}`",
            f"- Mean PN roles: `{summary['mean_pn_roles']:.2f}`",
            f"- Graph audit pass: `{summary['graph_audit_pass']}`",
            "",
            "## Boundary",
            "",
            "Only question text was used to generate task embeddings. No answer labels or API calls were used.",
            "",
            "## Next",
            "",
            summary["next_action"],
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit generated MMLU PN/PE graphs.")
    parser.add_argument("--model_dir", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--transfer_jsonl", default=DEFAULT_TRANSFER_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--details_jsonl", default=DEFAULT_DETAILS_JSONL)
    parser.add_argument("--num_tasks", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run_id", default="R187")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_audit(
        model_dir=args.model_dir,
        transfer_jsonl=args.transfer_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
        details_jsonl=args.details_jsonl,
        num_tasks=args.num_tasks,
        seed=args.seed,
        run_id=args.run_id,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
