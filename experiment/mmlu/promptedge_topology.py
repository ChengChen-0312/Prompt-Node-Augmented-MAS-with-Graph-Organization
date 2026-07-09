from __future__ import annotations

from typing import Any, Dict, List, Tuple

import networkx as nx
import torch
from torch_geometric.data import Data


PN_CHAIN: Tuple[str, str, str] = ("PN_Memory", "PN_Verifier", "PN_Router")


def inject_promptedge_topology(
    graph: nx.DiGraph,
    decision_exposure_policy: str = "terminal",
) -> nx.DiGraph:
    """Add first-class PromptNode/PromptEdge structure to a MMLU agent graph."""
    augmented = graph.copy()
    if not nx.is_directed_acyclic_graph(augmented):
        raise ValueError("PromptEdge topology requires a DAG input graph.")

    existing_roles = nx.get_node_attributes(augmented, "role")
    if set(PN_CHAIN).issubset(set(existing_roles.values())):
        augmented.graph["decision_exposure_policy"] = decision_exposure_policy
        return augmented

    base_nodes = list(augmented.nodes())
    next_id = (max(base_nodes) + 1) if base_nodes else 0
    pn_ids = {}
    for offset, role in enumerate(PN_CHAIN):
        node_id = next_id + offset
        pn_ids[role] = node_id
        augmented.add_node(
            node_id,
            role=role,
            constraint="first-class virtual PromptNode for MMLU graph organization",
            promptnode_type=role,
        )

    for source in base_nodes:
        augmented.add_edge(
            source,
            pn_ids["PN_Memory"],
            promptedge=True,
            promptedge_permission="read",
            promptedge_type="evidence_ledger_read",
            promptedge_text="Read upstream answer labels, rationales, uncertainty, and option bindings.",
        )
    augmented.add_edge(
        pn_ids["PN_Memory"],
        pn_ids["PN_Verifier"],
        promptedge=True,
        promptedge_permission="write",
        promptedge_type="ledger_to_verifier",
        promptedge_text="Write preserved target, options, and evidence ledger for verification.",
    )
    augmented.add_edge(
        pn_ids["PN_Verifier"],
        pn_ids["PN_Router"],
        promptedge=True,
        promptedge_permission="forward",
        promptedge_type="verified_evidence_forward",
        promptedge_text="Forward only target-preserved and option-bound evidence; suppress unsupported labels.",
    )

    for u, v in graph.edges():
        augmented.edges[u, v].setdefault("promptedge", False)
        augmented.edges[u, v].setdefault("promptedge_permission", "agent_to_agent")
        augmented.edges[u, v].setdefault("promptedge_type", "base_agent_edge")
        augmented.edges[u, v].setdefault("promptedge_text", "")

    if not nx.is_directed_acyclic_graph(augmented):
        raise ValueError("Injected PromptEdge topology produced a cyclic graph.")
    augmented.graph["decision_exposure_policy"] = decision_exposure_policy
    return augmented


def promptedge_topology_to_pyg(graph: nx.DiGraph, task_text: str) -> Data:
    """Convert a PN/PE MMLU topology graph to the repository's TestGraph Data shape."""
    ordered_nodes = list(nx.topological_sort(graph))
    node_to_idx = {node_id: idx for idx, node_id in enumerate(ordered_nodes)}

    pyg = Data()
    pyg.x = [
        {
            "role": graph.nodes[node_id].get("role", "Unknown"),
            "constraint": graph.nodes[node_id].get("constraint", ""),
        }
        for node_id in ordered_nodes
    ]

    ordered_edges: List[Tuple[int, int]] = list(graph.edges())
    edge_pairs = [[node_to_idx[u], node_to_idx[v]] for u, v in ordered_edges]
    pyg.edge_index = (
        torch.tensor(edge_pairs, dtype=torch.long).t().contiguous()
        if edge_pairs
        else torch.zeros((2, 0), dtype=torch.long)
    )
    pyg.promptedge_meta = [
        {
            "source_role": graph.nodes[u].get("role", "Unknown"),
            "target_role": graph.nodes[v].get("role", "Unknown"),
            "promptedge": bool(graph.edges[u, v].get("promptedge", False)),
            "permission": graph.edges[u, v].get("promptedge_permission", ""),
            "type": graph.edges[u, v].get("promptedge_type", ""),
            "text": graph.edges[u, v].get("promptedge_text", ""),
        }
        for u, v in ordered_edges
    ]
    pyg.task = task_text
    pyg.num_nodes = len(ordered_nodes)
    pyg.decision_exposure_policy = graph.graph.get("decision_exposure_policy", "terminal")
    return pyg
