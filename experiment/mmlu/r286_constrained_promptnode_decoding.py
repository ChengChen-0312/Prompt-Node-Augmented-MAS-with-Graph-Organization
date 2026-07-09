from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.mmlu_prompt_set import ROLE_DESCRIPTION
from experiment.mmlu.r187_promptedge_generated_graph_audit import (
    audit_generated_graph,
    load_tasks,
)
from experiment.utils import generate_graph, load_model


DEFAULT_MODEL_DIR = "experiment/mmlu/output/mmlu_promptnode_retrain_r283_e5_observed"
DEFAULT_TRANSFER_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r286_constrained_promptnode_decoding_selected.jsonl"
DEFAULT_CANDIDATES_JSONL = "experiment/mmlu/run_logs/mmlu_r286_constrained_promptnode_decoding_candidates.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r286_constrained_promptnode_decoding_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r286_constrained_promptnode_decoding_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        f.write(text)


def candidate_score(candidate: Dict[str, Any]) -> float:
    return (
        100.0 * float(bool(candidate.get("promptedge_contract_ready")))
        + 35.0 * float(bool(candidate.get("has_pn_chain")))
        + 20.0 * float(bool(candidate.get("has_all_pn_roles")))
        + 10.0 * float(bool(candidate.get("router_is_terminal")))
        + 5.0 * float(bool(candidate.get("has_any_pn")))
        + 3.0 * float(bool(candidate.get("is_dag")))
        + min(float(candidate.get("pn_role_count", 0)), 6.0)
    )


def select_best_candidate(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not candidates:
        raise ValueError("No candidates to select from.")
    return max(candidates, key=lambda row: (candidate_score(row), -int(row.get("candidate_index", 0))))


def describe_graph(graph: Any) -> Dict[str, Any]:
    nodes = [
        {"id": int(node), "role": str(data.get("role", ""))}
        for node, data in sorted(graph.nodes(data=True), key=lambda item: int(item[0]))
    ]
    edges = [
        {
            "source": int(src),
            "target": int(dst),
            "label": int(data.get("label", 1)),
        }
        for src, dst, data in sorted(
            graph.edges(data=True), key=lambda item: (int(item[0]), int(item[1]))
        )
    ]
    return {"nodes": nodes, "edges": edges}


def summarize_selected(
    selected_rows: List[Dict[str, Any]],
    candidate_rows: List[Dict[str, Any]],
    candidates_per_task: int,
    run_id: str = "R286",
) -> Dict[str, Any]:
    total = len(selected_rows)

    def count_selected(key: str) -> int:
        return sum(1 for row in selected_rows if row.get(key))

    task_to_candidates: Dict[str, List[Dict[str, Any]]] = {}
    for row in candidate_rows:
        task_to_candidates.setdefault(str(row.get("task_id")), []).append(row)

    tasks_with_any_ready = sum(
        1
        for rows in task_to_candidates.values()
        if any(row.get("promptedge_contract_ready") for row in rows)
    )

    selected_contract_ready = count_selected("promptedge_contract_ready")
    summary = {
        "run_id": run_id,
        "title": "MMLU constrained PromptNode graph decoding audit",
        "claim_boundary": (
            "No-API constrained decoding audit only. Candidate selection uses generated graph "
            "structure, not answer labels, and never adds nodes or edges."
        ),
        "no_api": True,
        "broad_api": False,
        "tasks": total,
        "candidates_per_task": candidates_per_task,
        "candidate_graphs": len(candidate_rows),
        "selected_dag_graphs": count_selected("is_dag"),
        "selected_with_any_pn": count_selected("has_any_pn"),
        "selected_with_all_pn_roles": count_selected("has_all_pn_roles"),
        "selected_with_pn_chain": count_selected("has_pn_chain"),
        "selected_with_terminal_router": count_selected("router_is_terminal"),
        "selected_contract_ready": selected_contract_ready,
        "selected_contract_ready_rate": selected_contract_ready / total if total else 0.0,
        "tasks_with_any_contract_ready_candidate": tasks_with_any_ready,
        "tasks_with_any_contract_ready_candidate_rate": tasks_with_any_ready / total if total else 0.0,
        "structural_claim_supported": total > 0 and selected_contract_ready / total >= 0.5,
        "accuracy_claim_supported": False,
        "api_eval_allowed_next": total > 0 and selected_contract_ready / total >= 0.5,
        "next_goal_audit_due": "R290",
    }
    summary["next_action"] = (
        "Run checkpoint-level API smoke on selected constrained graphs."
        if summary["api_eval_allowed_next"]
        else "Retrain or regularize the graph policy so the full PN chain appears before API evaluation."
    )
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R286 Constrained PromptNode Decoding Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- Candidates per task: `{summary['candidates_per_task']}`",
            f"- Candidate graphs: `{summary['candidate_graphs']}`",
            f"- Selected with any PN: `{summary['selected_with_any_pn']}`",
            f"- Selected with all PN roles: `{summary['selected_with_all_pn_roles']}`",
            f"- Selected with PN chain: `{summary['selected_with_pn_chain']}`",
            f"- Selected with terminal router: `{summary['selected_with_terminal_router']}`",
            f"- Selected contract-ready: `{summary['selected_contract_ready']}`",
            f"- Selected contract-ready rate: `{summary['selected_contract_ready_rate']:.3f}`",
            f"- Tasks with any contract-ready candidate: `{summary['tasks_with_any_contract_ready_candidate']}`",
            f"- API eval allowed next: `{summary['api_eval_allowed_next']}`",
            "",
            "## Boundary",
            "",
            "R286 does not add, delete, or relabel graph nodes. It only selects among graphs sampled from the retrained R283 checkpoint.",
            "",
            "## Next",
            "",
            summary["next_action"],
            "",
        ]
    )


def run(
    model_dir: str = DEFAULT_MODEL_DIR,
    transfer_jsonl: str = DEFAULT_TRANSFER_JSONL,
    num_tasks: int = 24,
    candidates_per_task: int = 16,
    seed: int = 42,
    selected_jsonl: str = DEFAULT_OUTPUT_JSONL,
    candidates_jsonl: str = DEFAULT_CANDIDATES_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    run_id: str = "R286",
) -> Dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    model = load_model(model_dir, ef=False)
    sentence_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    tasks = load_tasks(transfer_jsonl, num_tasks)
    selected_rows: List[Dict[str, Any]] = []
    candidate_rows: List[Dict[str, Any]] = []

    for task_idx, task in enumerate(tasks):
        task_embedding = torch.tensor(
            sentence_model.encode(task["question"]),
            device=model.args.device,
        ).float()
        generated = generate_graph(
            model,
            task_embedding,
            ROLE_DESCRIPTION,
            question_id=task_idx,
            num_samples=candidates_per_task,
            batch_size=candidates_per_task,
        )
        task_candidates: List[Dict[str, Any]] = []
        for candidate_idx, graph in enumerate(generated):
            audit = audit_generated_graph(graph)
            row = {
                "task_id": task["task_id"],
                "subject": task["subject"],
                "candidate_index": candidate_idx,
                "score": 0.0,
                **describe_graph(graph),
                "roles": audit.get("roles", []),
                "num_nodes": audit.get("num_nodes"),
                "num_edges": audit.get("num_edges"),
                **audit,
            }
            row["score"] = candidate_score(row)
            task_candidates.append(row)
            candidate_rows.append(row)
        selected = dict(select_best_candidate(task_candidates))
        selected["selected_by"] = "contract_constrained_decoding"
        selected_rows.append(selected)
        if (task_idx + 1) % 8 == 0:
            print(f"R286 progress: {task_idx + 1}/{len(tasks)} tasks", flush=True)

    summary = summarize_selected(selected_rows, candidate_rows, candidates_per_task, run_id=run_id)
    summary.update(
        {
            "model_dir": model_dir,
            "transfer_jsonl": transfer_jsonl,
            "num_tasks": num_tasks,
            "seed": seed,
            "selected_jsonl": selected_jsonl,
            "candidates_jsonl": candidates_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    _write_jsonl(selected_jsonl, selected_rows)
    _write_jsonl(candidates_jsonl, candidate_rows)
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run no-API constrained PromptNode decoding audit.")
    parser.add_argument("--model_dir", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--transfer_jsonl", default=DEFAULT_TRANSFER_JSONL)
    parser.add_argument("--num_tasks", type=int, default=24)
    parser.add_argument("--candidates_per_task", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--selected_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--candidates_jsonl", default=DEFAULT_CANDIDATES_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--run_id", default="R286")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
