from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import networkx as nx
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from experiment.mmlu.promptedge_topology import (
    inject_promptedge_topology,
    promptedge_topology_to_pyg,
)


DEFAULT_SOURCE_DIRS = [
    "experiment/ColdStartData_mmlu",
    "experiment/FinetuneData_mmlu",
]
DEFAULT_TRANSFER_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/promptedge_targets/mmlu_r183_promptedge_targets.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r183_promptedge_target_export_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r183_promptedge_target_export_report.md"
OPTION_LABELS = ("A", "B", "C", "D", "E")
MODEL_VISIBLE_ROUTER_FIELDS = [
    "question",
    "roles",
    "edges",
    "promptedge_meta",
    "promptedge_permissions",
    "decision_exposure_policy",
]
FORBIDDEN_ROUTER_VISIBLE_FIELDS = [
    "answer",
    "true_answer",
    "gold_answer",
    "is_correct",
    "predicted_answer",
    "baseline_is_correct",
    "task_id",
    "source_question_hash",
    "audit_label",
]


def normalize_question(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def question_hash(text: str) -> str:
    return sha256(normalize_question(text).encode("utf-8")).hexdigest()


def extract_option_labels(text: str) -> List[str]:
    labels = set(re.findall(r"(?:^|\s)(?:Option\s+)?([A-E])\s*[\):.]", str(text or "")))
    ordered = [label for label in OPTION_LABELS if label in labels]
    return ordered or ["A", "B", "C", "D"]


def build_router_final_schema(question: str) -> Dict[str, Any]:
    return {
        "schema_version": "r211_router_final_v1",
        "target_kind": "router_final_or_abstain",
        "router_action": "abstain",
        "target_option_label": "NONE",
        "allowed_option_labels": extract_option_labels(question) + ["NONE"],
        "override_label": False,
        "gold_answer_used": False,
        "model_visible_fields": list(MODEL_VISIBLE_ROUTER_FIELDS),
        "forbidden_model_visible_fields": list(FORBIDDEN_ROUTER_VISIBLE_FIELDS),
        "edge_permission_labels": ["read", "write", "forward"],
        "promptedge_text_policy": {
            "edge_text_as_prompt": True,
            "source_field": "promptedge_meta.text",
            "scope": "PromptEdge metadata only; no gold answer or correctness fields.",
        },
        "label_policy": (
            "Preserve-safe training target: PN_Router learns to abstain unless verified "
            "option evidence is available from non-leaking PromptNode/PromptEdge fields."
        ),
    }


def load_transfer_hashes(path: str) -> Set[str]:
    hashes: Set[str] = set()
    if not path or not os.path.exists(path):
        return hashes
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            for key in ("question", "task"):
                value = row.get(key)
                if value:
                    hashes.add(question_hash(value))
    return hashes


def data_to_nx(data: Any) -> nx.DiGraph:
    graph = nx.DiGraph()
    node_rows = list(getattr(data, "x", []))
    for idx, node in enumerate(node_rows):
        graph.add_node(
            idx,
            role=node.get("role", "Unknown"),
            constraint=node.get("constraint", ""),
        )

    edge_index = getattr(data, "edge_index", None)
    if edge_index is not None and edge_index.numel() > 0:
        for src, dst in edge_index.t().tolist():
            graph.add_edge(int(src), int(dst))
    return graph


def _get_question(data: Any) -> str:
    return str(getattr(data, "question", None) or getattr(data, "task", "") or "")


def build_target_record(
    source_path: str,
    data: Any,
    transfer_hashes: Set[str],
) -> Optional[Dict[str, Any]]:
    question = _get_question(data)
    q_hash = question_hash(question)
    if q_hash in transfer_hashes:
        return None

    base_graph = data_to_nx(data)
    augmented = inject_promptedge_topology(base_graph)
    pyg = promptedge_topology_to_pyg(augmented, task_text=question)

    roles = [node["role"] for node in pyg.x]
    promptedge_meta = list(getattr(pyg, "promptedge_meta", []))
    promptedge_permissions = sorted(
        {
            meta.get("permission", "")
            for meta in promptedge_meta
            if meta.get("promptedge") and meta.get("permission")
        }
    )

    return {
        "target_kind": "promptedge_preserve_safe_insert",
        "override_label": false_bool(False),
        "source_graph_path": source_path,
        "source_split_inferred": "mmlu_val_generated_r161",
        "source_question_hash": q_hash,
        "leakage_checked_against_transfer100": True,
        "transfer100_exact_question_overlap": False,
        "question": question,
        "mode": getattr(data, "mode", None),
        "is_correct": bool(getattr(data, "is_correct", False)),
        "num_nodes_before": base_graph.number_of_nodes(),
        "num_edges_before": base_graph.number_of_edges(),
        "num_nodes_after": len(roles),
        "num_edges_after": int(pyg.edge_index.shape[1]),
        "original_roles": [
            base_graph.nodes[node_id].get("role", "Unknown")
            for node_id in base_graph.nodes()
        ],
        "roles": roles,
        "pn_roles": [role for role in roles if role.startswith("PN_")],
        "edges": pyg.edge_index.t().tolist(),
        "decision_exposure_policy": getattr(pyg, "decision_exposure_policy", "terminal"),
        "promptedge_permissions": promptedge_permissions,
        "promptedge_meta": promptedge_meta,
        "router_final_schema": build_router_final_schema(question),
        "label_policy": (
            "Successful ARG graph is converted into a first-class PromptNode/PromptEdge "
            "organization target. Transfer100 answers are not used for training labels."
        ),
    }


def false_bool(value: bool) -> bool:
    return bool(value)


def iter_source_paths(source_dirs: Sequence[str]) -> List[str]:
    paths: List[str] = []
    for source_dir in source_dirs:
        paths.extend(glob.glob(os.path.join(source_dir, "*.pt")))
    return sorted(set(paths))


def export_targets(
    source_dirs: Sequence[str],
    transfer_jsonl: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
) -> Dict[str, Any]:
    transfer_hashes = load_transfer_hashes(transfer_jsonl)
    source_paths = iter_source_paths(source_dirs)
    records: List[Dict[str, Any]] = []
    filtered_transfer_overlap = 0
    failures: List[Dict[str, str]] = []

    for source_path in source_paths:
        try:
            data = torch.load(source_path, map_location="cpu", weights_only=False)
            record = build_target_record(source_path, data, transfer_hashes)
            if record is None:
                filtered_transfer_overlap += 1
                continue
            records.append(record)
        except Exception as exc:  # pragma: no cover - surfaced in summary for audit.
            failures.append({"source_graph_path": source_path, "error": repr(exc)})

    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    mode_counts = Counter(str(record.get("mode")) for record in records)
    role_counts = Counter(role for record in records for role in record["roles"])
    unique_questions = {record["source_question_hash"] for record in records}
    summary = {
        "run_id": "R183",
        "title": "MMLU PromptNode/PromptEdge target export manifest",
        "claim_boundary": (
            "Data export only. No API evaluation, no accuracy claim, and no claim that "
            "the exported insertion targets improve over ARG-Designer."
        ),
        "no_api": True,
        "broad_api": False,
        "source_dirs": list(source_dirs),
        "transfer_jsonl": transfer_jsonl,
        "output_jsonl": output_jsonl,
        "summary_json": summary_json,
        "report_md": report_md,
        "source_graphs": len(source_paths),
        "exported_graphs": len(records),
        "unique_exported_questions": len(unique_questions),
        "transfer_hashes": len(transfer_hashes),
        "filtered_transfer_overlap": filtered_transfer_overlap,
        "failures": failures,
        "failure_count": len(failures),
        "mode_counts": dict(sorted(mode_counts.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "pn_roles": ["PN_Memory", "PN_Verifier", "PN_Router"],
        "target_kind": "promptedge_preserve_safe_insert",
        "override_labels_exported": 0,
        "leakage_audit": {
            "exact_question_hash_against_transfer100": True,
            "source_metadata_available": False,
            "tail34_or_sync20_used": False,
            "transfer100_used_as_training_label": False,
        },
        "next_action": (
            "R184 should dry-run or train a PN-capable MMLU graph generator from this "
            "manifest after adapting the training loader to consume exported PN/PE targets."
        ),
    }

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
            "# R183 MMLU PromptNode/PromptEdge Target Export",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Source graphs: `{summary['source_graphs']}`",
            f"- Exported PN/PE target graphs: `{summary['exported_graphs']}`",
            f"- Unique exported questions: `{summary['unique_exported_questions']}`",
            f"- Transfer100 hashes checked: `{summary['transfer_hashes']}`",
            f"- Filtered exact transfer overlaps: `{summary['filtered_transfer_overlap']}`",
            f"- Failures: `{summary['failure_count']}`",
            f"- Target kind: `{summary['target_kind']}`",
            f"- Override labels exported: `{summary['override_labels_exported']}`",
            "",
            "## Leakage Boundary",
            "",
            "- Exact question hashes were checked against transfer100.",
            "- No tail34 or sync20 data is used.",
            "- Transfer100 answers are not used as training labels.",
            "- Source `.pt` files do not preserve original MMLU source metadata, so the audit is exact-question based rather than source-file/source-index based.",
            "",
            "## Next",
            "",
            summary["next_action"],
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export MMLU PromptEdge target manifest.")
    parser.add_argument("--source_dirs", nargs="+", default=DEFAULT_SOURCE_DIRS)
    parser.add_argument("--transfer_jsonl", default=DEFAULT_TRANSFER_JSONL)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = export_targets(
        source_dirs=args.source_dirs,
        transfer_jsonl=args.transfer_jsonl,
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
