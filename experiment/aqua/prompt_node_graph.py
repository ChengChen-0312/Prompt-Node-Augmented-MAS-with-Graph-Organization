import copy
from collections import Counter
from typing import Iterable

import networkx as nx


PN_ROLE_DESCRIPTIONS = {
    "PN_Memory": (
        "You are a virtual Prompt Node for evidence memory in a multi-agent graph. "
        "You store upstream agent outputs, extracted answer labels, target statements, "
        "and option-binding evidence. You are not a standalone math solver."
    ),
    "PN_Verifier": (
        "You are a virtual Prompt Node for verification in a multi-agent graph. "
        "You check target preservation, option binding, unsupported labels, and "
        "conflicts across upstream evidence. You are not a standalone math solver."
    ),
    "PN_Router": (
        "You are a virtual Prompt Node for communication routing in a multi-agent graph. "
        "You forward compact verified evidence to downstream agents or the final decision "
        "while suppressing unsupported or shifted-target evidence."
    ),
}

PN_ROLES = tuple(PN_ROLE_DESCRIPTIONS.keys())

REAL_AGENT_ROLES = (
    "Math Solver",
    "Mathematical Analyst",
    "Programming Expert",
    "Inspector",
)

PROMPT_EDGE_TYPES = (
    "agent_flow",
    "write_memory",
    "read_memory",
    "verify_contract",
    "forward_verified",
    "suppress_unsupported",
    "repair_option",
)


def is_prompt_node_role(role: str) -> bool:
    return role in PN_ROLE_DESCRIPTIONS or str(role).startswith("PN_")


def get_real_agent_roles(role_descriptions=None) -> tuple[str, ...]:
    if role_descriptions is None:
        return REAL_AGENT_ROLES
    return tuple(role for role in REAL_AGENT_ROLES if role in role_descriptions)


def infer_prompt_edge_type(source_role: str, target_role: str) -> str:
    source = str(source_role or "")
    target = str(target_role or "")
    if target == "PN_Memory" and not is_prompt_node_role(source):
        return "write_memory"
    if source == "PN_Memory" and target == "PN_Verifier":
        return "verify_contract"
    if source == "PN_Verifier" and target == "PN_Router":
        return "forward_verified"
    if source == "PN_Router" and target == "PN_Repair":
        return "repair_option"
    if is_prompt_node_role(source) or is_prompt_node_role(target):
        return "read_memory"
    return "agent_flow"


def summarize_prompt_edges(nx_graph: nx.Graph) -> dict[str, int]:
    counts = Counter()
    for _, _, data in nx_graph.edges(data=True):
        edge_type = data.get("prompt_edge_type") or data.get("prompt_edge") or "agent_flow"
        counts[str(edge_type)] += 1
    return dict(sorted(counts.items()))


def attach_prompt_edge_metadata(nx_graph: nx.Graph) -> nx.DiGraph:
    graph = nx.DiGraph(nx_graph)
    graph.graph.update(copy.deepcopy(getattr(nx_graph, "graph", {})))
    for source, target, data in graph.edges(data=True):
        source_role = graph.nodes[source].get("role", "")
        target_role = graph.nodes[target].get("role", "")
        edge_type = data.get("prompt_edge_type") or data.get("prompt_edge")
        if edge_type in {"write", "read", "forward"}:
            edge_type = infer_prompt_edge_type(source_role, target_role)
        elif edge_type not in PROMPT_EDGE_TYPES:
            edge_type = infer_prompt_edge_type(source_role, target_role)
        data["prompt_edge_type"] = edge_type
        data["prompt_edge"] = edge_type
        data.setdefault("label", 1)
    graph.graph["prompt_edge_type_counts"] = summarize_prompt_edges(graph)
    return graph


def _next_integer_node_ids(graph: nx.Graph, count: int) -> Iterable[int]:
    int_nodes = [node for node in graph.nodes if isinstance(node, int)]
    start = (max(int_nodes) + 1) if int_nodes else graph.number_of_nodes()
    return range(start, start + count)


def _copy_real_agent_subgraph(nx_graph: nx.Graph) -> nx.DiGraph:
    source = nx.DiGraph(nx_graph)
    graph = nx.DiGraph()
    graph.graph.update(copy.deepcopy(getattr(nx_graph, "graph", {})))

    real_nodes = [
        node
        for node, data in source.nodes(data=True)
        if not is_prompt_node_role(data.get("role", ""))
    ]
    mapping = {old_id: new_id for new_id, old_id in enumerate(real_nodes)}

    for old_id, new_id in mapping.items():
        graph.add_node(new_id, **copy.deepcopy(source.nodes[old_id]))

    for src, dst, data in source.edges(data=True):
        if src in mapping and dst in mapping:
            graph.add_edge(mapping[src], mapping[dst], **copy.deepcopy(data))

    return graph


def canonicalize_prompt_node_topology(
    nx_graph: nx.Graph, policy: str = "none"
) -> nx.DiGraph:
    if policy in (None, "none"):
        return copy.deepcopy(nx_graph)
    if policy not in {"canonicalize_generated", "canonicalize_or_insert"}:
        raise ValueError(f"Unsupported prompt node topology policy: {policy}")

    graph = nx.DiGraph(nx_graph)
    has_prompt_nodes = any(
        is_prompt_node_role(data.get("role", ""))
        for _, data in graph.nodes(data=True)
    )
    if policy == "canonicalize_generated" and not has_prompt_nodes:
        return copy.deepcopy(nx_graph)

    real_graph = _copy_real_agent_subgraph(graph)
    if real_graph.number_of_nodes() == 0:
        return real_graph

    normalized = augment_graph_with_prompt_nodes(
        real_graph, policy="memory_verifier_router"
    )
    normalized.graph["prompt_node_topology_policy"] = policy
    normalized.graph["canonicalized_prompt_nodes"] = True
    return normalized


def augment_graph_with_prompt_nodes(
    nx_graph: nx.Graph, policy: str = "memory_verifier_router"
) -> nx.DiGraph:
    if policy == "none":
        return copy.deepcopy(nx_graph)
    if policy not in {"memory_verifier", "memory_verifier_router"}:
        raise ValueError(f"Unsupported prompt node policy: {policy}")

    graph = nx.DiGraph(nx_graph)
    graph.graph.update(copy.deepcopy(getattr(nx_graph, "graph", {})))
    original_nodes = [
        node
        for node, data in graph.nodes(data=True)
        if not is_prompt_node_role(data.get("role", ""))
    ]
    if not original_nodes:
        return graph

    selected_roles = PN_ROLES[:2] if policy == "memory_verifier" else PN_ROLES
    prompt_node_ids = list(_next_integer_node_ids(graph, len(selected_roles)))

    for node_id, role in zip(prompt_node_ids, selected_roles):
        graph.add_node(
            node_id,
            role=role,
            label=-1,
            constraint=PN_ROLE_DESCRIPTIONS[role],
            is_prompt_node=True,
            prompt_node_policy=policy,
        )

    memory_node = prompt_node_ids[0]
    verifier_node = prompt_node_ids[1]
    for node in original_nodes:
        graph.add_edge(node, memory_node, label=1, prompt_edge="write")
    graph.add_edge(memory_node, verifier_node, label=1, prompt_edge="read")

    if policy == "memory_verifier_router":
        router_node = prompt_node_ids[2]
        graph.add_edge(verifier_node, router_node, label=1, prompt_edge="forward")

    graph.graph["prompt_node_policy"] = policy
    graph.graph["prompt_node_roles"] = list(selected_roles)
    return graph


def score_prompt_node_candidate_graph(nx_graph: nx.Graph) -> dict:
    roles = [data.get("role", "") for _, data in nx_graph.nodes(data=True)]
    role_counts = Counter(roles)
    real_roles = [role for role in roles if not is_prompt_node_role(role)]
    pn_roles = [role for role in roles if is_prompt_node_role(role)]

    role_coverage = (
        len(set(real_roles).intersection(REAL_AGENT_ROLES)) / max(len(REAL_AGENT_ROLES), 1)
    )
    pn_coverage = len(set(pn_roles).intersection(PN_ROLES)) / max(len(PN_ROLES), 1)

    num_nodes = nx_graph.number_of_nodes()
    num_edges = nx_graph.number_of_edges()
    if num_nodes <= 1:
        connectivity = 0.0
        density = 0.0
    else:
        graph_for_connectivity = nx.DiGraph(nx_graph)
        connectivity = 1.0 if nx.is_weakly_connected(graph_for_connectivity) else 0.0
        max_edges = num_nodes * (num_nodes - 1)
        density = num_edges / max(max_edges, 1)

    density_balance = max(0.0, 1.0 - abs(density - 0.35) / 0.35)
    repeated_roles = sum(count - 1 for count in role_counts.values() if count > 1)
    redundancy_penalty = repeated_roles / max(num_nodes, 1)
    cost_penalty = 0.04 * max(num_nodes - 2, 0) + 0.02 * max(num_edges - 1, 0)

    score = (
        2.0 * role_coverage
        + 1.5 * pn_coverage
        + 0.8 * connectivity
        + 0.6 * density_balance
        - 0.8 * redundancy_penalty
        - cost_penalty
    )
    return {
        "score": round(float(score), 6),
        "role_coverage": round(float(role_coverage), 6),
        "pn_coverage": round(float(pn_coverage), 6),
        "connectivity": round(float(connectivity), 6),
        "density": round(float(density), 6),
        "density_balance": round(float(density_balance), 6),
        "redundancy_penalty": round(float(redundancy_penalty), 6),
        "cost_penalty": round(float(cost_penalty), 6),
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "roles": roles,
    }


def select_prompt_node_candidate_graph(graphs: list[nx.Graph]) -> tuple[nx.Graph, list[dict]]:
    if not graphs:
        raise ValueError("No candidate graphs to select from")

    scored = []
    for idx, graph in enumerate(graphs):
        record = score_prompt_node_candidate_graph(graph)
        record["candidate_index"] = idx
        scored.append(record)

    best = max(scored, key=lambda item: (item["score"], -item["candidate_index"]))
    return graphs[best["candidate_index"]], scored
