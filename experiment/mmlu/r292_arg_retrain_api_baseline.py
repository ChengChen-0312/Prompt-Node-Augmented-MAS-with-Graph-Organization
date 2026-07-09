from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.mmlu_prompt_set import ROLE_DESCRIPTION
from experiment.mmlu.r187_promptedge_generated_graph_audit import audit_generated_graph
from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from experiment.mmlu.r286_constrained_promptnode_decoding import describe_graph
from experiment.mmlu.transfer_dataset import MMLUTransferDataset
from experiment.utils import convert_to_pyg_graph, generate_graph, load_model
from mas_framework.graph.graph import TestGraph
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


DEFAULT_MODEL_DIR = "experiment/mmlu/output/mmlu_arg_retrain_r282_e5_observed"
DEFAULT_TRANSFER_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r292_arg_retrain_first24_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r292_arg_retrain_first24_api_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r292_arg_retrain_first24_api_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(_repo_path(path)), exist_ok=True)
    with open(_repo_path(path), "w", encoding="utf-8") as f:
        f.write(text)


def normalize_task_id(record: Dict[str, Any], fallback: int) -> str:
    return str(record.get("task_id") or record.get("id") or f"task_{fallback}")


def summarize_records(
    rows: List[Dict[str, Any]],
    api_cost: float,
    prompt_tokens: int,
    completion_tokens: int,
) -> Dict[str, Any]:
    evaluated = [row for row in rows if row.get("is_correct") is not None and not row.get("api_error")]
    correct = sum(1 for row in evaluated if row.get("is_correct"))
    return {
        "records": len(rows),
        "evaluated_records": len(evaluated),
        "correct": correct,
        "accuracy": correct / len(evaluated) if evaluated else None,
        "api_errors": sum(1 for row in rows if row.get("api_error")),
        "api_cost": round(float(api_cost), 6),
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "mean_nodes": sum(float(row.get("num_nodes", 0.0)) for row in rows) / len(rows) if rows else 0.0,
        "mean_edges": sum(float(row.get("num_edges", 0.0)) for row in rows) / len(rows) if rows else 0.0,
    }


async def _run_one(
    model: Any,
    sentence_model: SentenceTransformer,
    dataset: MMLUTransferDataset,
    record: Dict[str, Any],
    index: int,
    decision_method: str,
    llm_name: str,
    num_rounds: int,
    decision_exposure_policy: str,
) -> Dict[str, Any]:
    task_input = dataset.record_to_input(record)
    true_answer = dataset.record_to_target_answer(record)
    task_embedding = torch.tensor(
        sentence_model.encode(task_input["task"]),
        device=model.args.device,
    ).float()
    generated = generate_graph(
        model,
        task_embedding,
        ROLE_DESCRIPTION,
        question_id=index,
        num_samples=1,
        batch_size=1,
    )
    graph = generated[0]
    graph_desc = describe_graph(graph)
    audit = audit_generated_graph(graph)
    pyg_data = convert_to_pyg_graph(graph, task_input["task"])
    pyg_data.decision_exposure_policy = decision_exposure_policy
    test_graph = TestGraph(
        domain="mmlu",
        llm_name=llm_name,
        decision_method=decision_method,
        pyg_data=pyg_data,
    )

    before_cost = Cost.instance().value
    before_prompt = PromptTokens.instance().value
    before_completion = CompletionTokens.instance().value
    started = time.time()
    try:
        raw_answer = await test_graph.arun(task_input, num_rounds=num_rounds)
        predicted = dataset.postprocess_answer(raw_answer)
        api_error = ""
    except Exception as exc:  # pragma: no cover
        raw_answer = ""
        predicted = ""
        api_error = f"{type(exc).__name__}: {exc}"
    return {
        "task_id": normalize_task_id(record, index),
        "subject": record.get("subject"),
        "true_answer": true_answer,
        "predicted_answer": predicted,
        "is_correct": (predicted == true_answer) if not api_error else None,
        "api_error": api_error,
        "raw_answer": raw_answer,
        "decision_method": decision_method,
        "llm_name": llm_name,
        "num_rounds": num_rounds,
        "decision_exposure_policy": decision_exposure_policy,
        "duration_s": round(time.time() - started, 3),
        "cost_delta": round(float(Cost.instance().value - before_cost), 6),
        "prompt_tokens_delta": int(PromptTokens.instance().value - before_prompt),
        "completion_tokens_delta": int(CompletionTokens.instance().value - before_completion),
        **graph_desc,
        **audit,
    }


async def run_async(
    model_dir: str = DEFAULT_MODEL_DIR,
    transfer_jsonl: str = DEFAULT_TRANSFER_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    limit_tasks: int = 24,
    eval_batch_size: int = 2,
    decision_method: str = "FinalRefer",
    llm_name: str = "gpt-4o-2024-08-06",
    num_rounds: int = 1,
    decision_exposure_policy: str = "all",
    seed: int = 42,
    execute_api: bool = False,
    run_id: str = "R292",
) -> Dict[str, Any]:
    if not execute_api:
        raise RuntimeError("Pass --execute_api to run R292 ARG retrain API baseline.")
    load_env_values(env_file)
    import mas_framework.llm.gpt_chat as gpt_chat

    gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
    gpt_chat.MINE_API_KEY = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not gpt_chat.MINE_API_KEY:
        raise RuntimeError("Missing API_KEY or OPENAI_API_KEY after loading env file.")

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    model = load_model(model_dir, ef=False)
    sentence_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    dataset = MMLUTransferDataset(_repo_path(transfer_jsonl))
    records = list(dataset)[:limit_tasks]

    outputs: List[Dict[str, Any]] = []
    for start in range(0, len(records), eval_batch_size):
        batch = records[start : start + eval_batch_size]
        batch_outputs = await asyncio.gather(
            *[
                _run_one(
                    model,
                    sentence_model,
                    dataset,
                    record,
                    index=start + offset,
                    decision_method=decision_method,
                    llm_name=llm_name,
                    num_rounds=num_rounds,
                    decision_exposure_policy=decision_exposure_policy,
                )
                for offset, record in enumerate(batch)
            ]
        )
        outputs.extend(batch_outputs)
        print(f"{run_id} progress: {len(outputs)}/{len(records)} tasks", flush=True)
        write_jsonl(output_jsonl, outputs)

    summary = summarize_records(
        outputs,
        api_cost=Cost.instance().value,
        prompt_tokens=int(PromptTokens.instance().value),
        completion_tokens=int(CompletionTokens.instance().value),
    )
    summary.update(
        {
            "run_id": run_id,
            "title": "MMLU R282 ARG retrain first24 API baseline",
            "claim_boundary": (
                "Checkpoint-level ARG retrain baseline on transfer100 first24. "
                "Used for matched comparison with constrained PromptNode replay."
            ),
            "no_api": False,
            "broad_api": False,
            "model_dir": model_dir,
            "transfer_jsonl": transfer_jsonl,
            "limit_tasks": limit_tasks,
            "seed": seed,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
            "env_values_logged": False,
            "decision_method": decision_method,
            "llm_name": llm_name,
            "num_rounds": num_rounds,
            "decision_exposure_policy": decision_exposure_policy,
        }
    )
    write_jsonl(output_jsonl, outputs)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R292 MMLU ARG Retrain API Baseline",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['records']}`",
            f"- Correct: `{summary['correct']}`",
            f"- Accuracy: `{summary['accuracy']}`",
            f"- API errors: `{summary['api_errors']}`",
            f"- Cost: `${summary['api_cost']:.6f}`",
            f"- Prompt/completion tokens: `{summary['prompt_tokens']}/{summary['completion_tokens']}`",
            f"- Mean nodes/edges: `{summary['mean_nodes']:.2f}/{summary['mean_edges']:.2f}`",
            f"- Decision method: `{summary['decision_method']}`",
            "",
        ]
    )


def run(**kwargs: Any) -> Dict[str, Any]:
    return asyncio.run(run_async(**kwargs))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R292 ARG retrain API baseline.")
    parser.add_argument("--model_dir", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--transfer_jsonl", default=DEFAULT_TRANSFER_JSONL)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--limit_tasks", type=int, default=24)
    parser.add_argument("--eval_batch_size", type=int, default=2)
    parser.add_argument("--decision_method", default="FinalRefer")
    parser.add_argument("--llm_name", default="gpt-4o-2024-08-06")
    parser.add_argument("--num_rounds", type=int, default=1)
    parser.add_argument("--decision_exposure_policy", default="all")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--execute_api", action="store_true")
    parser.add_argument("--run_id", default="R292")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
