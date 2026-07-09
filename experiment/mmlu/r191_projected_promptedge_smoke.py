from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
from typing import Any, Dict, List

import networkx as nx
import numpy as np
import torch
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_MODEL_DIR = "experiment/mmlu/output/mmlu_promptedge_pn_graph_policy_r188_e5"
DEFAULT_TRANSFER_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_BASELINE_JSONL = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r191_projected_promptedge_smoke_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r191_projected_promptedge_smoke_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r191_projected_promptedge_smoke_report.md"


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_baseline_lookup(path: str) -> Dict[str, Dict[str, Any]]:
    return {str(row.get("task_id")): row for row in load_jsonl(path)}


def select_first_n_records(records: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    return list(records[:n])


def select_records_by_task_ids(records: List[Dict[str, Any]], task_ids: List[str]) -> List[Dict[str, Any]]:
    by_id = {str(row.get("task_id") or row.get("id")): row for row in records}
    return [by_id[task_id] for task_id in task_ids]


def _ensure_env_loaded(env_file: str) -> None:
    if env_file and os.path.exists(env_file):
        load_dotenv(env_file, override=True)
    try:
        from mas_framework.llm import gpt_chat

        gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
        gpt_chat.MINE_API_KEY = (
            os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        ).strip()
    except Exception:
        pass


def _extract_task_id(record: Dict[str, Any], fallback: int) -> str:
    return str(record.get("task_id") or record.get("id") or f"task_{fallback}")


def _graph_logging_view(graph: nx.DiGraph) -> Dict[str, Any]:
    node_order = list(nx.topological_sort(graph)) if nx.is_directed_acyclic_graph(graph) else list(graph.nodes())
    return {
        "roles": [graph.nodes[node_id].get("role", "Unknown") for node_id in node_order],
        "edges": [[int(src), int(dst)] for src, dst in graph.edges()],
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
    }


def build_promptedge_logging_payload(
    raw_graph: nx.DiGraph,
    projected_graph: nx.DiGraph,
    pyg: Any,
    task_text: str,
) -> Dict[str, Any]:
    from experiment.mmlu.export_promptedge_targets import build_router_final_schema

    promptedge_meta = list(getattr(pyg, "promptedge_meta", []))
    promptedge_permissions = sorted(
        {
            meta.get("permission", "")
            for meta in promptedge_meta
            if meta.get("promptedge") and meta.get("permission")
        }
    )
    router_final_schema = build_router_final_schema(task_text)
    return {
        "raw_graph": _graph_logging_view(raw_graph),
        "projected_graph": _graph_logging_view(projected_graph),
        "promptedge_meta": promptedge_meta,
        "promptedge_permissions": promptedge_permissions,
        "router_final_schema": router_final_schema,
        "router_final_abstain_only": (
            router_final_schema.get("router_action") == "abstain"
            and router_final_schema.get("target_option_label") == "NONE"
        ),
        "promptedge_text_as_edge_prompt": bool(
            router_final_schema.get("promptedge_text_policy", {}).get("edge_text_as_prompt")
        ),
    }


async def run_smoke(
    model_dir: str,
    transfer_jsonl: str,
    baseline_jsonl: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
    env_file: str,
    llm_name: str,
    decision_method: str,
    max_tasks: int,
    task_ids: List[str],
    dry_run: bool,
    seed: int,
    decision_exposure_policy: str,
    run_id: str = "",
) -> Dict[str, Any]:
    _ensure_env_loaded(env_file)

    from experiment.mmlu.mmlu_prompt_set import ROLE_DESCRIPTION
    from experiment.mmlu.r187_promptedge_generated_graph_audit import audit_generated_graph
    from experiment.mmlu.r189_promptedge_projection_audit import (
        project_generated_graph_to_promptedge_contract,
    )
    from experiment.mmlu.promptedge_topology import promptedge_topology_to_pyg
    from experiment.mmlu.transfer_dataset import MMLUTransferDataset
    from experiment.utils import generate_graph, load_model
    from mas_framework.graph.graph import TestGraph
    from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    dataset = MMLUTransferDataset(transfer_jsonl)
    selection_policy = "task_ids_explicit" if task_ids else "first_n_no_answer_filter"
    records = (
        select_records_by_task_ids(list(dataset), task_ids)
        if task_ids
        else select_first_n_records(list(dataset), max_tasks)
    )
    baseline_lookup = load_baseline_lookup(baseline_jsonl)
    model = load_model(model_dir, ef=False)
    sentence_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    details: List[Dict[str, Any]] = []
    effective_run_id = run_id or ("R191" if dry_run else "R192")

    for idx, record in enumerate(records):
        task_id = _extract_task_id(record, idx)
        input_dict = dataset.record_to_input(record)
        task_text = input_dict["task"]
        task_embedding = torch.tensor(
            sentence_model.encode(task_text),
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
        pyg = promptedge_topology_to_pyg(projected_graph, task_text)
        pyg.decision_exposure_policy = decision_exposure_policy
        promptedge_logging = build_promptedge_logging_payload(
            raw_graph=raw_graph,
            projected_graph=projected_graph,
            pyg=pyg,
            task_text=task_text,
        )

        baseline = baseline_lookup.get(task_id, {})
        true_answer = dataset.record_to_target_answer(record)
        raw_answer = []
        predicted_answer = ""
        is_correct = None
        if not dry_run:
            graph = TestGraph(
                domain="mmlu",
                llm_name=llm_name,
                decision_method=decision_method,
                pyg_data=pyg,
            )
            raw_answer = await graph.arun(input_dict, num_rounds=1)
            predicted_answer = dataset.postprocess_answer(raw_answer)
            is_correct = predicted_answer == true_answer

        details.append(
            {
                "run_id": effective_run_id,
                "dry_run": dry_run,
                "selection_policy": selection_policy,
                "task_id": task_id,
                "subject": record.get("subject", ""),
                "true_answer": true_answer,
                "baseline_predicted_answer": baseline.get("predicted_answer"),
                "baseline_is_correct": baseline.get("is_correct"),
                "raw_graph_audit": raw_audit,
                "projected_graph_audit": projected_audit,
                **promptedge_logging,
                "decision_method": decision_method,
                "decision_exposure_policy": decision_exposure_policy,
                "llm_name": llm_name,
                "raw_answer": raw_answer,
                "predicted_answer": predicted_answer,
                "is_correct": is_correct,
            }
        )

    evaluated = [row for row in details if row["is_correct"] is not None]
    fixes = sum(
        1 for row in evaluated if row["baseline_is_correct"] is False and row["is_correct"] is True
    )
    harms = sum(
        1 for row in evaluated if row["baseline_is_correct"] is True and row["is_correct"] is False
    )
    summary = {
        "run_id": effective_run_id,
        "title": "Projected PromptEdge MMLU transfer smoke",
        "claim_boundary": (
            "Diagnostic smoke only. No paper-level accuracy claim; task selection is first-N "
            "and not answer-based."
        ),
        "dry_run": dry_run,
        "no_api": dry_run,
        "broad_api": False,
        "model_dir": model_dir,
        "transfer_jsonl": transfer_jsonl,
        "baseline_jsonl": baseline_jsonl,
        "max_tasks": max_tasks,
        "task_ids": task_ids,
        "selection_policy": selection_policy,
        "tasks_prepared": len(details),
        "tasks_evaluated": len(evaluated),
        "projected_contract_ready": sum(
            1 for row in details if row["projected_graph_audit"]["promptedge_contract_ready"]
        ),
        "baseline_correct": sum(1 for row in evaluated if row["baseline_is_correct"] is True),
        "projected_correct": sum(1 for row in evaluated if row["is_correct"] is True),
        "fixes": fixes,
        "harms": harms,
        "cost": Cost.instance().value,
        "prompt_tokens": int(PromptTokens.instance().value),
        "completion_tokens": int(CompletionTokens.instance().value),
        "output_jsonl": output_jsonl,
        "next_action": (
            "If dry_run=true, run the same command without --dry_run only if the user accepts "
            "the diagnostic cost. If dry_run=false, analyze fix/harm as diagnostic-only."
        ),
    }

    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
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
            f"# {summary['run_id']} Projected PromptEdge MMLU Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Dry run: `{summary['dry_run']}`",
            f"- Tasks prepared: `{summary['tasks_prepared']}`",
            f"- Tasks evaluated: `{summary['tasks_evaluated']}`",
            f"- Projected contract-ready: `{summary['projected_contract_ready']}/{summary['tasks_prepared']}`",
            f"- Baseline correct: `{summary['baseline_correct']}`",
            f"- Projected correct: `{summary['projected_correct']}`",
            f"- Fixes: `{summary['fixes']}`",
            f"- Harms: `{summary['harms']}`",
            f"- Cost: `${summary['cost']:.6f}`",
            f"- Prompt/completion tokens: `{summary['prompt_tokens']}/{summary['completion_tokens']}`",
            "",
            "## Boundary",
            "",
            "The first-N selection is not answer-based. This smoke is diagnostic and cannot be used as a paper-level accuracy claim.",
            "",
            "## Next",
            "",
            summary["next_action"],
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run projected PromptEdge MMLU smoke.")
    parser.add_argument("--model_dir", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--transfer_jsonl", default=DEFAULT_TRANSFER_JSONL)
    parser.add_argument("--baseline_jsonl", default=DEFAULT_BASELINE_JSONL)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--llm_name", default="gpt-4o-2024-08-06")
    parser.add_argument("--decision_method", default="FinalRefer")
    parser.add_argument("--decision_exposure_policy", default="all")
    parser.add_argument("--max_tasks", type=int, default=4)
    parser.add_argument("--task_ids", nargs="*", default=[])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--run_id", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = asyncio.run(
        run_smoke(
            model_dir=args.model_dir,
            transfer_jsonl=args.transfer_jsonl,
            baseline_jsonl=args.baseline_jsonl,
            output_jsonl=args.output_jsonl,
            summary_json=args.summary_json,
            report_md=args.report_md,
            env_file=args.env_file,
            llm_name=args.llm_name,
            decision_method=args.decision_method,
            max_tasks=args.max_tasks,
            task_ids=args.task_ids,
            dry_run=args.dry_run,
            seed=args.seed,
            decision_exposure_policy=args.decision_exposure_policy,
            run_id=args.run_id,
        )
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
