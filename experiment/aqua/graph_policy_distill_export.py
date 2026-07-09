import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402
from experiment.aqua.offline_utility_selector import (  # noqa: E402
    DEFAULT_CONTRACT_METHOD_KEYS,
    load_prefix_result_sets,
)


PROMPT_NODE_ROLES = {"PN_Memory", "PN_Verifier", "PN_Router"}

PROMPT_NODE_SPEC_TEMPLATES = {
    "PN_Memory": {
        "identity_type": "Memory",
        "runtime_behavior": "shared_state",
        "insertion_pattern": "memory_bridge",
        "content_schema": {
            "kept_fields": ["intermediate_facts", "option_bindings", "agent_claims"],
            "compression_rule": "retain option-critical facts and conflicting claims",
        },
        "permissions": ["read", "write"],
        "budget": {"max_tokens": 256, "max_updates": 3},
        "lifecycle_actions": ["update", "compress", "merge", "prune"],
    },
    "PN_Verifier": {
        "identity_type": "Instruction/Verifier",
        "runtime_behavior": "verify",
        "insertion_pattern": "aggregator_checkpoint",
        "content_schema": {
            "kept_fields": ["supported_option", "binding_status", "conflict_reason"],
            "compression_rule": "retain exact/equivalent option-binding evidence",
        },
        "permissions": ["read", "write", "forward"],
        "budget": {"max_tokens": 384, "max_updates": 2},
        "lifecycle_actions": ["update", "prune", "upgrade"],
    },
    "PN_Router": {
        "identity_type": "Agent-like",
        "runtime_behavior": "Router",
        "insertion_pattern": "conflict_router",
        "content_schema": {
            "kept_fields": ["route_decision", "forwarded_option", "confidence_signal"],
            "compression_rule": "retain only route-relevant option evidence",
        },
        "permissions": ["read", "forward"],
        "budget": {"max_tokens": 256, "max_updates": 2},
        "lifecycle_actions": ["update", "merge", "prune"],
    },
}

DISALLOWED_POLICY_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
    "r035_selected_prediction",
    "r035_selected_source",
}


def _is_prompt_node_role(role: Any) -> bool:
    role_text = str(role)
    return role_text in PROMPT_NODE_ROLES or role_text.startswith("PN_")


def _prompt_node_spec(role: str, node_index: int) -> Dict[str, Any]:
    template = PROMPT_NODE_SPEC_TEMPLATES.get(
        role,
        {
            "identity_type": "Agent-like",
            "runtime_behavior": "auxiliary",
            "insertion_pattern": "task_local",
            "content_schema": {
                "kept_fields": ["task_state"],
                "compression_rule": "retain task-relevant state",
            },
            "permissions": ["read", "forward"],
            "budget": {"max_tokens": 256, "max_updates": 1},
            "lifecycle_actions": ["update", "prune"],
        },
    )
    return {"node_index": node_index, "role": role, **template}


def _edge_permissions(source_role: str, target_role: str) -> List[str]:
    source_is_pn = _is_prompt_node_role(source_role)
    target_is_pn = _is_prompt_node_role(target_role)
    if not source_is_pn and target_is_pn:
        return ["write"]
    if source_role == "PN_Memory":
        return ["read"]
    if target_role == "PN_Memory":
        return ["write"]
    if source_role == "PN_Verifier" and target_role == "PN_Router":
        return ["read", "forward"]
    if target_role == "PN_Verifier":
        return ["read", "write"]
    if source_role == "PN_Router":
        return ["forward"]
    if source_is_pn and not target_is_pn:
        return ["forward"]
    return ["read"]


def normalize_graph_for_policy(graph: Dict[str, Any]) -> Dict[str, Any]:
    roles = [str(role) for role in (graph.get("roles") or [])]
    raw_edges = graph.get("edges") or []
    edges: List[List[int]] = []
    edge_role_pairs: List[str] = []
    prompt_node_edge_role_pairs: List[str] = []

    for edge in raw_edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            continue
        source, target = int(edge[0]), int(edge[1])
        if source < 0 or target < 0 or source >= len(roles) or target >= len(roles):
            continue
        edges.append([source, target])
        pair = f"{roles[source]}->{roles[target]}"
        edge_role_pairs.append(pair)
        if _is_prompt_node_role(roles[source]) or _is_prompt_node_role(roles[target]):
            prompt_node_edge_role_pairs.append(pair)

    prompt_node_roles = [role for role in roles if _is_prompt_node_role(role)]
    prompt_node_specs = [
        _prompt_node_spec(role, node_index)
        for node_index, role in enumerate(roles)
        if _is_prompt_node_role(role)
    ]
    prompt_node_edge_permissions = {
        pair: _edge_permissions(*pair.split("->", 1))
        for pair in prompt_node_edge_role_pairs
    }
    role_counts = Counter(roles)
    prompt_counts = Counter(prompt_node_roles)
    sorted_edges = sorted(edges)
    graph_signature = (
        "|".join(sorted(set(roles)))
        + "::"
        + ",".join(f"{source}->{target}" for source, target in sorted_edges)
    )
    return {
        "roles": roles,
        "edges": sorted_edges,
        "num_nodes": len(roles),
        "num_edges": len(sorted_edges),
        "role_counts": dict(sorted(role_counts.items())),
        "prompt_node_roles": prompt_node_roles,
        "prompt_node_role_counts": dict(sorted(prompt_counts.items())),
        "prompt_node_specs": prompt_node_specs,
        "num_prompt_nodes": len(prompt_node_roles),
        "edge_role_pairs": sorted(edge_role_pairs),
        "prompt_node_edge_role_pairs": sorted(prompt_node_edge_role_pairs),
        "prompt_node_edge_permissions": dict(sorted(prompt_node_edge_permissions.items())),
        "num_prompt_node_edges": len(prompt_node_edge_role_pairs),
        "graph_signature": graph_signature,
    }


def _policy_target(training_row: Dict[str, Any], policy_graph: Dict[str, Any]) -> Dict[str, Any]:
    training_target = str(training_row.get("training_target"))
    return {
        "candidate_label": 1 if training_target == "preferred_graph" else 0,
        "training_target": training_target,
        "objective_reward": training_row.get("objective_score"),
        "score_components": training_row.get("score_components", {}),
        "score_margin_to_next": training_row.get("score_margin_to_next"),
        "roles": policy_graph["roles"],
        "edges": policy_graph["edges"],
        "prompt_node_roles": policy_graph["prompt_node_roles"],
        "prompt_node_role_counts": policy_graph["prompt_node_role_counts"],
        "prompt_node_specs": policy_graph["prompt_node_specs"],
        "edge_role_pairs": policy_graph["edge_role_pairs"],
        "prompt_node_edge_role_pairs": policy_graph["prompt_node_edge_role_pairs"],
        "prompt_node_edge_permissions": policy_graph["prompt_node_edge_permissions"],
        "graph_signature": policy_graph["graph_signature"],
    }


def _field_violates(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in DISALLOWED_POLICY_FIELDS:
                return True
            if _field_violates(child):
                return True
    elif isinstance(value, list):
        return any(_field_violates(child) for child in value)
    return False


def build_policy_rows(
    training_rows: Sequence[Dict[str, Any]],
    result_sets: Dict[str, Dict[str, Dict[str, Any]]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    missing_graph_rows = 0
    positive_prompt_node_rows = 0
    positive_prompt_node_spec_rows = 0
    positive_prompt_node_edge_permission_rows = 0
    target_counts: Counter[str] = Counter()
    positive_role_counts: Counter[str] = Counter()
    positive_edge_pair_counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()
    slice_counts: Counter[str] = Counter()
    signatures_by_label: Dict[str, Counter[str]] = defaultdict(Counter)

    for training_row in training_rows:
        method = str(training_row.get("candidate_method"))
        task_id = str(training_row.get("task_id"))
        result_record = result_sets.get(method, {}).get(task_id, {})
        graph = result_record.get("generated_graph")
        if not isinstance(graph, dict):
            missing_graph_rows += 1
            continue

        policy_graph = normalize_graph_for_policy(graph)
        target = _policy_target(training_row, policy_graph)
        training_target = target["training_target"]
        candidate_label = target["candidate_label"]
        slice_prefix = str(training_row.get("slice_prefix"))
        target_counts[training_target] += 1
        method_counts[method] += 1
        slice_counts[slice_prefix] += 1
        signatures_by_label[str(candidate_label)][policy_graph["graph_signature"]] += 1
        if candidate_label == 1:
            if policy_graph["num_prompt_nodes"] > 0:
                positive_prompt_node_rows += 1
            if policy_graph["prompt_node_specs"]:
                positive_prompt_node_spec_rows += 1
            if policy_graph["prompt_node_edge_permissions"]:
                positive_prompt_node_edge_permission_rows += 1
            positive_role_counts.update(policy_graph["prompt_node_roles"])
            positive_edge_pair_counts.update(policy_graph["prompt_node_edge_role_pairs"])

        rows.append(
            {
                "task_id": task_id,
                "slice_prefix": slice_prefix,
                "candidate_method": method,
                "policy_input": {
                    "slice_prefix": slice_prefix,
                    "question": result_record.get("question"),
                    "candidate_method": method,
                },
                "graph_policy_target": target,
                "claim_boundary": (
                    "Graph-policy distillation target derived from label-free PromptNode contract objective. "
                    "The policy row excludes gold answers, predicted answers, router options, audit labels, and correctness fields."
                ),
            }
        )

    outcome_field_violations = sum(1 for row in rows if _field_violates(row))
    positive_rows = sum(1 for row in rows if row["graph_policy_target"]["candidate_label"] == 1)
    summary = {
        "source_training_rows": len(training_rows),
        "policy_rows": len(rows),
        "missing_graph_rows": missing_graph_rows,
        "positive_policy_rows": positive_rows,
        "positive_prompt_node_policy_rows": positive_prompt_node_rows,
        "positive_prompt_node_spec_rows": positive_prompt_node_spec_rows,
        "positive_prompt_node_edge_permission_rows": positive_prompt_node_edge_permission_rows,
        "target_counts": dict(sorted(target_counts.items())),
        "candidate_method_counts": dict(sorted(method_counts.items())),
        "slice_counts": dict(sorted(slice_counts.items())),
        "positive_prompt_node_role_counts": dict(sorted(positive_role_counts.items())),
        "positive_prompt_node_edge_role_pair_counts": dict(sorted(positive_edge_pair_counts.items())),
        "unique_positive_graph_signatures": len(signatures_by_label["1"]),
        "unique_negative_graph_signatures": len(signatures_by_label["0"]),
        "outcome_field_violations": outcome_field_violations,
        "excluded_policy_fields": sorted(DISALLOWED_POLICY_FIELDS),
        "claim_boundary": (
            "Node/edge graph-policy supervision only. These rows make PromptNode virtual nodes part of "
            "the graph-generation target before execution; they do not report answer accuracy."
        ),
    }
    return rows, summary


def build_first200_policy_rows(
    training_rows: Sequence[Dict[str, Any]],
    base_dir: str = "experiment/aqua",
    prefixes: Sequence[str] = ("aqua_100", "aqua_next100"),
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    result_sets: Dict[str, Dict[str, Dict[str, Any]]] = {
        method: {} for method in DEFAULT_CONTRACT_METHOD_KEYS
    }
    for prefix in prefixes:
        prefix_sets = load_prefix_result_sets(prefix, base_dir)
        for method in DEFAULT_CONTRACT_METHOD_KEYS:
            result_sets.setdefault(method, {}).update(prefix_sets.get(method, {}))
    rows, summary = build_policy_rows(training_rows, result_sets)
    summary["prefixes"] = list(prefixes)
    summary["method_keys"] = list(DEFAULT_CONTRACT_METHOD_KEYS)
    return rows, summary


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _format_counts(counts: Dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def render_report(summary: Dict[str, Any], output_jsonl: str, input_rows: str) -> str:
    return "\n".join(
        [
            "# AQuA First200 PromptNode Graph-Policy Distillation Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Input graph-objective rows: `{input_rows}`",
            f"- Output policy rows: `{output_jsonl}`",
            f"- Source training rows: `{summary['source_training_rows']}`",
            f"- Policy rows: `{summary['policy_rows']}`",
            f"- Positive policy rows: `{summary['positive_policy_rows']}`",
            f"- Positive PromptNode policy rows: `{summary['positive_prompt_node_policy_rows']}`",
            f"- Positive PromptNode spec rows: `{summary['positive_prompt_node_spec_rows']}`",
            f"- Positive PromptNode edge-permission rows: `{summary['positive_prompt_node_edge_permission_rows']}`",
            f"- Missing graph rows: `{summary['missing_graph_rows']}`",
            f"- Outcome-field violations: `{summary['outcome_field_violations']}`",
            f"- Target counts: `{_format_counts(summary.get('target_counts', {}))}`",
            f"- Positive PromptNode role counts: `{_format_counts(summary.get('positive_prompt_node_role_counts', {}))}`",
            f"- Unique positive graph signatures: `{summary['unique_positive_graph_signatures']}`",
            "",
            "## Why This Matters",
            "",
            "R052 converts the label-free graph objective into explicit node and edge supervision. "
            "Each row contains the task-visible input and a graph-policy target with roles, edges, PromptNode role counts, "
            "PromptNode edge role pairs, graph signature, candidate label, and objective reward. "
            "The export deliberately removes gold answers, predicted answers, router options, direct-majority options, "
            "audit labels, and correctness fields.",
            "",
            "This is closer to the intended PromptNode design than R051's shallow graph-ranker replay: the virtual node is "
            "now a trainable graph-organization target before execution. It is still not an accuracy result; the next step "
            "is to train the ARG-Designer node/edge generator on these targets and validate on tail34 or transfer data.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export PromptNode graph-policy node/edge supervision from label-free graph objectives."
    )
    parser.add_argument(
        "--input-jsonl",
        default="experiment/aqua/aqua_first200_graph_objective_training_rows.jsonl",
    )
    parser.add_argument("--base-dir", default="experiment/aqua")
    parser.add_argument("--prefix", action="append", dest="prefixes", default=[])
    parser.add_argument(
        "--output-jsonl",
        default="experiment/aqua/aqua_first200_graph_policy_distill_rows.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_graph_policy_distill_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_graph_policy_distill_report.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prefixes = args.prefixes or ["aqua_100", "aqua_next100"]
    training_rows = load_jsonl_rows(args.input_jsonl)
    rows, summary = build_first200_policy_rows(training_rows, base_dir=args.base_dir, prefixes=prefixes)
    payload = {
        "input_jsonl": args.input_jsonl,
        "output_jsonl": args.output_jsonl,
        **summary,
    }
    write_jsonl(args.output_jsonl, rows)
    write_json(args.summary_json, payload)
    write_text(args.report_md, render_report(payload, output_jsonl=args.output_jsonl, input_rows=args.input_jsonl))
    print(
        "Exported graph-policy distillation rows: "
        f"rows={summary['policy_rows']} positives={summary['positive_policy_rows']} "
        f"positive_promptnode={summary['positive_prompt_node_policy_rows']} "
        f"violations={summary['outcome_field_violations']}"
    )


if __name__ == "__main__":
    main()
