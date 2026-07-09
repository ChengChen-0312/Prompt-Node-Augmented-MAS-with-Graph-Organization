import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.aqua_prompt_set import ROLE_DESCRIPTION  # noqa: E402
from experiment.aqua.clean_fix_graph_template_export import load_jsonl_rows  # noqa: E402
from experiment.aqua.prompt_node_graph import PN_ROLE_DESCRIPTIONS, is_prompt_node_role  # noqa: E402


RULE_NAME = "r083_tail34_clean_fix_template_candidate_materialize"

DEFAULT_TEMPLATE_JSONL = "experiment/aqua/aqua_first200_r082_clean_fix_graph_templates.jsonl"
DEFAULT_TASK_SPLIT_JSON = "experiment/aqua/task_split_aqua_tail34.json"
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r083_clean_fix_template_candidates.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r083_clean_fix_template_candidates_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r083_clean_fix_template_candidates_report.md"

FORBIDDEN_RUNTIME_FIELDS = {
    "answer",
    "answers",
    "audit_label",
    "baseline_is_solved",
    "clean_label",
    "direct_majority",
    "is_solved",
    "predicted_answer",
    "question",
    "raw_response",
    "router_option",
    "task_text",
    "true_answer",
}

REQUIRED_PROMPTNODE_IDENTITIES = {"Memory", "Instruction/Verifier", "Agent-like"}


def record_has_forbidden_field(value: Any, forbidden_fields: set[str] = FORBIDDEN_RUNTIME_FIELDS) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden_fields:
                return True
            if record_has_forbidden_field(child, forbidden_fields):
                return True
    elif isinstance(value, list):
        return any(record_has_forbidden_field(child, forbidden_fields) for child in value)
    return False


def _template_sort_key(template: Dict[str, Any]) -> Tuple[int, int, str]:
    return (
        -int(template.get("support_count") or 0),
        -len(template.get("prompt_node_specs") or []),
        str(template.get("graph_signature") or ""),
    )


def _normalize_edges(edges: Sequence[Sequence[Any]]) -> List[List[int]]:
    normalized = []
    for edge in edges:
        if len(edge) != 2:
            raise ValueError(f"Invalid template edge: {edge}")
        normalized.append([int(edge[0]), int(edge[1])])
    return normalized


def _constraint_for_role(role: str) -> str:
    if role in PN_ROLE_DESCRIPTIONS:
        return PN_ROLE_DESCRIPTIONS[role]
    return ROLE_DESCRIPTION.get(role, "")


def _fallback_permissions(source_role: str, target_role: str) -> List[str]:
    if not is_prompt_node_role(source_role) and target_role == "PN_Memory":
        return ["write"]
    if source_role == "PN_Memory" and target_role == "PN_Verifier":
        return ["read"]
    if source_role == "PN_Verifier" and target_role == "PN_Router":
        return ["read", "forward"]
    if is_prompt_node_role(source_role) or is_prompt_node_role(target_role):
        return ["read"]
    return []


def _edge_permissions(
    source_role: str, target_role: str, template_permissions: Dict[str, Sequence[str]]
) -> List[str]:
    key = f"{source_role}->{target_role}"
    permissions = template_permissions.get(key)
    if permissions:
        return list(permissions)
    return _fallback_permissions(source_role, target_role)


def template_has_full_promptnode_specs(template: Dict[str, Any]) -> bool:
    specs = template.get("prompt_node_specs") or []
    identities = {str(spec.get("identity_type")) for spec in specs}
    if not REQUIRED_PROMPTNODE_IDENTITIES.issubset(identities):
        return False
    for spec in specs:
        if not spec.get("permissions"):
            return False
        if not spec.get("budget"):
            return False
        if not spec.get("lifecycle_actions"):
            return False
    return True


def template_has_full_edge_permissions(template: Dict[str, Any]) -> bool:
    roles = list(template.get("roles") or [])
    edges = _normalize_edges(template.get("edges") or [])
    permissions = dict(template.get("prompt_node_edge_permissions") or {})
    for source, target in edges:
        source_role = roles[source]
        target_role = roles[target]
        if is_prompt_node_role(source_role) or is_prompt_node_role(target_role):
            if not _edge_permissions(source_role, target_role, permissions):
                return False
    return True


def template_to_executable_record(template: Dict[str, Any], rank: int) -> Dict[str, Any]:
    roles = list(template.get("roles") or [])
    if not roles:
        raise ValueError("Template has no roles")
    edges = _normalize_edges(template.get("edges") or [])
    template_permissions = dict(template.get("prompt_node_edge_permissions") or {})

    nodes = [
        {
            "node_index": index,
            "role": role,
            "constraint": _constraint_for_role(role),
            "is_prompt_node": bool(is_prompt_node_role(role)),
        }
        for index, role in enumerate(roles)
    ]

    edge_records = []
    edge_permissions = {}
    for source, target in edges:
        source_role = roles[source]
        target_role = roles[target]
        permissions = _edge_permissions(source_role, target_role, template_permissions)
        edge_key = f"{source_role}->{target_role}"
        if permissions:
            edge_permissions[edge_key] = permissions
        edge_records.append(
            {
                "source": source,
                "target": target,
                "source_role": source_role,
                "target_role": target_role,
                "permissions": permissions,
                "prompt_edge": permissions[0] if permissions else None,
                "label": 1,
            }
        )

    return {
        "rank": int(rank),
        "graph_signature": str(template.get("graph_signature") or ""),
        "support_count": int(template.get("support_count") or 0),
        "support_slice_counts": dict(template.get("support_slice_counts") or {}),
        "support_candidate_method_counts": dict(template.get("support_candidate_method_counts") or {}),
        "decision_exposure_policy": "terminal",
        "graph_source": "r082_clean_fix_template",
        "prompt_node_topology_policy": "clean_fix_template",
        "prompt_node_roles": list(template.get("prompt_node_roles") or []),
        "prompt_node_specs": list(template.get("prompt_node_specs") or []),
        "graph": {
            "roles": roles,
            "nodes": nodes,
            "edges": edges,
            "edge_records": edge_records,
            "edge_permissions": edge_permissions,
        },
        "claim_boundary": (
            "Executable-ready PromptNode graph candidate derived from R082 template support. "
            "It does not include the task question, true answer, prediction, audit label, or correctness."
        ),
    }


def candidate_record_to_networkx(candidate: Dict[str, Any]):
    import networkx as nx

    graph_record = candidate.get("graph") or {}
    roles = list(graph_record.get("roles") or [])
    nodes = list(graph_record.get("nodes") or [])
    edges = list(graph_record.get("edge_records") or [])
    specs_by_index = {
        int(spec.get("node_index")): spec
        for spec in candidate.get("prompt_node_specs") or []
        if spec.get("node_index") is not None
    }

    graph = nx.DiGraph()
    if nodes:
        node_iter = nodes
    else:
        node_iter = [
            {
                "node_index": index,
                "role": role,
                "constraint": _constraint_for_role(role),
                "is_prompt_node": bool(is_prompt_node_role(role)),
            }
            for index, role in enumerate(roles)
        ]

    for node in node_iter:
        node_index = int(node["node_index"])
        role = node.get("role") or roles[node_index]
        node_attrs = {
            "role": role,
            "constraint": node.get("constraint") or _constraint_for_role(role),
            "label": -1 if is_prompt_node_role(role) else 0,
            "is_prompt_node": bool(node.get("is_prompt_node") or is_prompt_node_role(role)),
        }
        spec = specs_by_index.get(node_index)
        if spec:
            node_attrs.update(
                {
                    "identity_type": spec.get("identity_type"),
                    "runtime_behavior": spec.get("runtime_behavior"),
                    "insertion_pattern": spec.get("insertion_pattern"),
                    "content_schema": spec.get("content_schema"),
                    "permissions": spec.get("permissions"),
                    "budget": spec.get("budget"),
                    "lifecycle_actions": spec.get("lifecycle_actions"),
                    "prompt_node_spec": spec,
                }
            )
        graph.add_node(node_index, **node_attrs)

    if edges:
        for edge in edges:
            source = int(edge["source"])
            target = int(edge["target"])
            graph.add_edge(
                source,
                target,
                label=int(edge.get("label", 1)),
                prompt_edge=edge.get("prompt_edge"),
                permissions=list(edge.get("permissions") or []),
                source_role=edge.get("source_role"),
                target_role=edge.get("target_role"),
            )
    else:
        for source, target in _normalize_edges(graph_record.get("edges") or []):
            graph.add_edge(source, target, label=1)

    graph.graph.update(
        {
            "forced_template_candidate": True,
            "graph_signature": candidate.get("graph_signature"),
            "graph_source": candidate.get("graph_source"),
            "selected_candidate_rank": int(candidate.get("rank") or 0),
            "support_count": int(candidate.get("support_count") or 0),
            "decision_exposure_policy": candidate.get("decision_exposure_policy") or "terminal",
            "prompt_node_topology_policy": candidate.get("prompt_node_topology_policy")
            or "clean_fix_template",
            "prompt_node_roles": list(candidate.get("prompt_node_roles") or []),
            "prompt_node_specs": list(candidate.get("prompt_node_specs") or []),
            "prompt_node_edge_permissions": dict(graph_record.get("edge_permissions") or {}),
            "canonicalized_prompt_nodes": True,
        }
    )
    return graph


def build_tail34_template_candidates(
    templates: Sequence[Dict[str, Any]],
    task_indices: Sequence[int],
    top_k: int = 5,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    sorted_templates = sorted(list(templates), key=_template_sort_key)
    selected_templates = sorted_templates[:top_k]
    candidates = [
        template_to_executable_record(template, rank=index + 1)
        for index, template in enumerate(selected_templates)
    ]

    rows = []
    for dataset_index in task_indices:
        rows.append(
            {
                "task_id": f"task_{int(dataset_index)}",
                "dataset_index": int(dataset_index),
                "candidate_rule": RULE_NAME,
                "template_source_jsonl": DEFAULT_TEMPLATE_JSONL,
                "candidates": candidates,
                "claim_boundary": (
                    "This row materializes clean-fix PromptNode graph templates for future forced execution. "
                    "It is not an answer-accuracy result."
                ),
            }
        )

    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "template_source_count": len(templates),
        "num_tasks": len(task_indices),
        "top_k": top_k,
        "total_candidates": len(task_indices) * len(candidates),
        "unique_candidate_templates": len(candidates),
        "templates_with_full_promptnode_specs": sum(
            1 for template in selected_templates if template_has_full_promptnode_specs(template)
        ),
        "templates_with_full_edge_permissions": sum(
            1 for template in selected_templates if template_has_full_edge_permissions(template)
        ),
        "forbidden_field_violations": sum(
            1 for row in rows if record_has_forbidden_field(row, FORBIDDEN_RUNTIME_FIELDS)
        ),
        "forbidden_runtime_fields": sorted(FORBIDDEN_RUNTIME_FIELDS),
        "claim_boundary": (
            "R083 materializes R082 clean-fix PromptNode templates on AQuA tail34. "
            "It validates graph metadata coverage only; accuracy requires a subsequent forced-execution run."
        ),
    }
    return rows, summary


def load_task_indices(path: str) -> List[int]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    indices = payload.get("test_indices")
    if not indices:
        raise ValueError(f"Task split file has no test_indices: {path}")
    return [int(index) for index in indices]


def build_tail34_candidates_from_files(
    template_jsonl: str = DEFAULT_TEMPLATE_JSONL,
    task_split_json: str = DEFAULT_TASK_SPLIT_JSON,
    top_k: int = 5,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    templates = load_jsonl_rows(template_jsonl)
    task_indices = load_task_indices(task_split_json)
    rows, summary = build_tail34_template_candidates(templates, task_indices, top_k=top_k)
    summary["template_jsonl"] = template_jsonl
    summary["task_split_json"] = task_split_json
    return rows, summary


def write_json(path: str, payload: Dict[str, Any]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_text(path: str, text: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def render_report(rows: Sequence[Dict[str, Any]], summary: Dict[str, Any], output_jsonl: str) -> str:
    first_candidates = rows[0]["candidates"] if rows else []
    table_rows = [
        "| `{rank}` | `{support}` | `{nodes}` | `{edges}` | `{signature}` |".format(
            rank=candidate["rank"],
            support=candidate["support_count"],
            nodes=len(candidate["graph"]["roles"]),
            edges=len(candidate["graph"]["edges"]),
            signature=candidate["graph_signature"],
        )
        for candidate in first_candidates
    ]
    return "\n".join(
        [
            "# R083 Tail34 Clean-Fix PromptNode Template Candidates",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Template source: `{summary.get('template_jsonl')}`",
            f"- Task split: `{summary.get('task_split_json')}`",
            f"- Output candidates: `{output_jsonl}`",
            f"- Tail34 tasks: `{summary['num_tasks']}`",
            f"- Template source count: `{summary['template_source_count']}`",
            f"- Top-K per task: `{summary['top_k']}`",
            f"- Total materialized candidates: `{summary['total_candidates']}`",
            f"- Selected templates with full PromptNode specs: `{summary['templates_with_full_promptnode_specs']}`",
            f"- Selected templates with edge permissions: `{summary['templates_with_full_edge_permissions']}`",
            f"- Forbidden-field violations: `{summary['forbidden_field_violations']}`",
            "",
            "| Rank | Support | Nodes | Edges | Signature |",
            "| ---: | ---: | ---: | ---: | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R083 closes the metadata gap exposed by R081 without claiming an accuracy gain: every tail34 task now has "
            "clean-fix-derived PromptNode graph candidates with first-class node identities, permissions, budgets, and "
            "lifecycle actions. The next accuracy-bearing step is to add a forced-template execution hook and run a "
            "small smoke before a full tail34 evaluation.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materialize R082 clean-fix PromptNode graph templates as tail34 candidate graphs."
    )
    parser.add_argument("--template-jsonl", default=DEFAULT_TEMPLATE_JSONL)
    parser.add_argument("--task-split-json", default=DEFAULT_TASK_SPLIT_JSON)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows, summary = build_tail34_candidates_from_files(
        template_jsonl=args.template_jsonl,
        task_split_json=args.task_split_json,
        top_k=args.top_k,
    )
    write_jsonl(args.output_jsonl, rows)
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(rows, summary, args.output_jsonl))
    print(
        "Materialized tail34 clean-fix template candidates: "
        f"tasks={summary['num_tasks']} top_k={summary['top_k']} "
        f"total_candidates={summary['total_candidates']} "
        f"violations={summary['forbidden_field_violations']}"
    )


if __name__ == "__main__":
    main()
