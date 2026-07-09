import argparse
import json
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple

import networkx as nx
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.aqua_prompt_set import ROLE_DESCRIPTION  # noqa: E402
from experiment.aqua.graph_objective_pairwise_export import load_jsonl_rows  # noqa: E402
from experiment.utils import convert_to_pyg_graph  # noqa: E402


PROMPT_NODE_ROLES = {"PN_Memory", "PN_Verifier", "PN_Router"}

FORBIDDEN_PT_FIELDS = {
    "true_answer",
    "predicted_answer",
    "router_option",
    "direct_majority",
    "audit_label",
    "clean_label",
    "is_solved",
    "baseline_is_solved",
}


def _safe_id(value: Any) -> str:
    text = str(value or "unknown")
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_") or "unknown"


def _is_prompt_node_role(role: Any) -> bool:
    role_text = str(role)
    return role_text in PROMPT_NODE_ROLES or role_text.startswith("PN_")


def policy_target_to_networkx_graph(target: Dict[str, Any]) -> nx.DiGraph:
    graph = nx.DiGraph()
    roles = [str(role) for role in target.get("roles") or []]
    for index, role in enumerate(roles):
        graph.add_node(
            index,
            role=role,
            constraint=ROLE_DESCRIPTION.get(role, ""),
            label=role,
        )

    for edge in target.get("edges") or []:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            continue
        source, target_node = int(edge[0]), int(edge[1])
        if source < 0 or target_node < 0 or source >= len(roles) or target_node >= len(roles):
            continue
        graph.add_edge(source, target_node, label=0)

    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Graph-policy target must be a DAG for ARGDesigner finetuning")

    graph.graph["is_graph_policy_target"] = True
    graph.graph["graph_signature"] = target.get("graph_signature")
    graph.graph["candidate_label"] = target.get("candidate_label")
    graph.graph["training_target"] = target.get("training_target")
    graph.graph["objective_reward"] = target.get("objective_reward")
    graph.graph["num_prompt_nodes"] = sum(1 for role in roles if _is_prompt_node_role(role))
    prompt_node_specs = list(target.get("prompt_node_specs") or [])
    graph.graph["prompt_node_specs"] = {
        int(spec.get("node_index")): spec
        for spec in prompt_node_specs
        if spec.get("node_index") is not None
    }
    graph.graph["prompt_node_spec_list"] = prompt_node_specs
    graph.graph["prompt_node_edge_permissions"] = dict(
        target.get("prompt_node_edge_permissions") or {}
    )
    return graph


def _field_violates(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PT_FIELDS:
                return True
            if _field_violates(child):
                return True
    elif isinstance(value, list):
        return any(_field_violates(child) for child in value)
    return False


def _attach_policy_metadata(pyg: Any, row: Dict[str, Any], graph: nx.DiGraph, export_index: int) -> Any:
    policy_input = row.get("policy_input") or {}
    target = row.get("graph_policy_target") or {}
    question = str(policy_input.get("question") or "")
    pyg.question = question
    pyg.task = question
    pyg.mode = "PromptNodeGraphPolicy"
    pyg.agent_nums = int(graph.number_of_nodes())
    pyg.policy_label = int(target.get("candidate_label", 0) or 0)
    pyg.training_target = str(target.get("training_target"))
    pyg.objective_reward = target.get("objective_reward")
    pyg.graph_signature = target.get("graph_signature")
    pyg.prompt_node_specs = list(target.get("prompt_node_specs") or [])
    pyg.prompt_node_edge_permissions = dict(target.get("prompt_node_edge_permissions") or {})
    pyg.source_task_id = str(row.get("task_id"))
    pyg.source_slice_prefix = str(row.get("slice_prefix"))
    pyg.source_candidate_method = str(row.get("candidate_method"))
    pyg.export_index = export_index
    return pyg


def export_positive_policy_pt_dataset(
    policy_rows: Sequence[Dict[str, Any]],
    output_dir: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    os.makedirs(output_dir, exist_ok=True)
    exported: List[Dict[str, Any]] = []
    skipped_non_positive = 0
    promptnode_files = 0
    promptnode_spec_files = 0
    promptnode_edge_permission_files = 0
    role_counts: Counter[str] = Counter()
    signature_counts: Counter[str] = Counter()

    for row in policy_rows:
        target = row.get("graph_policy_target") or {}
        if int(target.get("candidate_label", 0) or 0) != 1:
            skipped_non_positive += 1
            continue

        graph = policy_target_to_networkx_graph(target)
        pyg = convert_to_pyg_graph(graph, str((row.get("policy_input") or {}).get("question") or ""))
        pyg = _attach_policy_metadata(pyg, row, graph, len(exported))
        if _field_violates(pyg.to_dict() if hasattr(pyg, "to_dict") else pyg.__dict__):
            raise ValueError(f"Forbidden answer/audit field found in PyG export for {row.get('task_id')}")

        roles = [node.get("role") for node in pyg.x]
        role_counts.update(role for role in roles if _is_prompt_node_role(role))
        if any(_is_prompt_node_role(role) for role in roles):
            promptnode_files += 1
        if target.get("prompt_node_specs"):
            promptnode_spec_files += 1
        if target.get("prompt_node_edge_permissions"):
            promptnode_edge_permission_files += 1
        signature = str(target.get("graph_signature"))
        signature_counts[signature] += 1
        filename = (
            f"r053_{len(exported):04d}_{_safe_id(row.get('slice_prefix'))}_"
            f"{_safe_id(row.get('task_id'))}_{_safe_id(row.get('candidate_method'))}_policy.pt"
        )
        path = os.path.join(output_dir, filename)
        torch.save(pyg, path)
        exported.append(
            {
                "path": path,
                "filename": filename,
                "task_id": row.get("task_id"),
                "slice_prefix": row.get("slice_prefix"),
                "candidate_method": row.get("candidate_method"),
                "num_nodes": graph.number_of_nodes(),
                "num_edges": graph.number_of_edges(),
                "prompt_node_roles": [role for role in roles if _is_prompt_node_role(role)],
                "graph_signature": signature,
            }
        )

    summary = {
        "source_policy_rows": len(policy_rows),
        "exported_pt_files": len(exported),
        "skipped_non_positive_rows": skipped_non_positive,
        "promptnode_pt_files": promptnode_files,
        "promptnode_spec_pt_files": promptnode_spec_files,
        "promptnode_edge_permission_pt_files": promptnode_edge_permission_files,
        "positive_prompt_node_role_counts": dict(sorted(role_counts.items())),
        "unique_positive_graph_signatures": len(signature_counts),
        "output_dir": output_dir,
        "outcome_field_violations": sum(1 for item in exported if _field_violates(item)),
        "excluded_pt_fields": sorted(FORBIDDEN_PT_FIELDS),
        "claim_boundary": (
            "ARGDesigner-compatible PyG finetune files generated from positive label-free PromptNode "
            "graph-policy targets. Files contain graph roles/edges and task text, not gold answers, predictions, "
            "router options, audit labels, or correctness fields."
        ),
    }
    return exported, summary


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


def render_report(summary: Dict[str, Any], manifest_jsonl: str) -> str:
    return "\n".join(
        [
            "# AQuA First200 PromptNode Graph-Policy PyG Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Output directory: `{summary['output_dir']}`",
            f"- Manifest JSONL: `{manifest_jsonl}`",
            f"- Source policy rows: `{summary['source_policy_rows']}`",
            f"- Exported `.pt` files: `{summary['exported_pt_files']}`",
            f"- Skipped non-positive rows: `{summary['skipped_non_positive_rows']}`",
            f"- PromptNode `.pt` files: `{summary['promptnode_pt_files']}`",
            f"- PromptNode spec `.pt` files: `{summary['promptnode_spec_pt_files']}`",
            f"- PromptNode edge-permission `.pt` files: `{summary['promptnode_edge_permission_pt_files']}`",
            f"- Positive PromptNode role counts: `{_format_counts(summary.get('positive_prompt_node_role_counts', {}))}`",
            f"- Unique positive graph signatures: `{summary['unique_positive_graph_signatures']}`",
            f"- Outcome-field violations: `{summary['outcome_field_violations']}`",
            "",
            "## Why This Matters",
            "",
            "R053 turns R052's node/edge policy rows into the actual `.pt` graph files consumed by "
            "`AquaGraphDataset(pretrain=False)`. This closes the interface gap between the paper idea and the "
            "ARG-Designer training pipeline: PromptNodes are now available as train-time graph nodes and edges.",
            "",
            "This export still does not report answer accuracy. It prepares a compatible finetune directory for the next "
            "step: train or fine-tune the ARG-Designer graph generator, then run same-model AQuA tail34 or transfer validation.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export positive PromptNode graph-policy targets as ARGDesigner-compatible PyG .pt files."
    )
    parser.add_argument(
        "--input-jsonl",
        default="experiment/aqua/aqua_first200_graph_policy_distill_rows.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        default="experiment/FinetuneData_AQuA_PN_GraphPolicy_R053",
    )
    parser.add_argument(
        "--manifest-jsonl",
        default="experiment/aqua/aqua_first200_graph_policy_pt_manifest.jsonl",
    )
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_first200_graph_policy_pt_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_first200_graph_policy_pt_report.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_jsonl_rows(args.input_jsonl)
    exported, summary = export_positive_policy_pt_dataset(rows, args.output_dir)
    payload = {
        "input_jsonl": args.input_jsonl,
        "manifest_jsonl": args.manifest_jsonl,
        **summary,
    }
    write_jsonl(args.manifest_jsonl, exported)
    write_json(args.summary_json, payload)
    write_text(args.report_md, render_report(payload, args.manifest_jsonl))
    print(
        "Exported PromptNode graph-policy PyG files: "
        f"files={summary['exported_pt_files']} promptnode={summary['promptnode_pt_files']} "
        f"violations={summary['outcome_field_violations']} output_dir={args.output_dir}"
    )


if __name__ == "__main__":
    main()
