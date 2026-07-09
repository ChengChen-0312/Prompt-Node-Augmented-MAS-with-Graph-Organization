import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import mas_framework.agents  # noqa: F401
import mas_framework.prompt.AQuA_prompt_set  # noqa: F401
from datasets.aqua_dataset import aqua_get_predict
from mas_framework.agents.agent_registry import AgentRegistry
from mas_framework.utils.globals import Cost, PromptTokens, CompletionTokens


def parse_args():
    parser = argparse.ArgumentParser(description="Replay PromptNode final authority on saved AQuA ARG outputs.")
    parser.add_argument("--input_file", default="aqua_sync20_eval20_results.jsonl")
    parser.add_argument("--output_file", default="aqua_sync20_promptnode_replay_results.jsonl")
    parser.add_argument("--llm_name", default="gpt-4o-2024-08-06")
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def load_rows(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_spatial_info(row):
    spatial_info = {}
    for idx, agent in enumerate(row.get("agent_outputs", []), start=1):
        outputs = agent.get("outputs") or []
        output = outputs[-1] if outputs else ""
        spatial_info[f"producer_{idx}"] = {
            "role": agent.get("role", "Unknown"),
            "output": output,
        }
    return spatial_info


async def main():
    args = parse_args()
    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    rows = load_rows(args.input_file)
    if args.limit:
        rows = rows[:args.limit]

    results = []
    solved = 0
    changed = 0
    fixes = 0
    harms = 0

    for row in rows:
        decision = AgentRegistry.get("PromptNodeFinalRefer", domain="aqua", llm_name=args.llm_name)
        raw = await decision._async_execute(
            {"task": row["question"]},
            build_spatial_info(row),
            {},
        )
        pred = aqua_get_predict(raw)
        gold = row["true_answer"]
        baseline_pred = row.get("predicted_answer")
        correct = pred == gold
        baseline_correct = row.get("is_solved", baseline_pred == gold)
        solved += int(correct)
        changed += int(pred != baseline_pred)
        fixes += int(correct and not baseline_correct)
        harms += int((not correct) and baseline_correct)
        results.append({
            "task_id": row["task_id"],
            "question": row["question"],
            "true_answer": gold,
            "baseline_predicted_answer": baseline_pred,
            "baseline_is_solved": baseline_correct,
            "promptnode_predicted_answer": pred,
            "promptnode_raw_response": raw,
            "promptnode_is_solved": correct,
            "changed": pred != baseline_pred,
        })
        print(
            f"{row['task_id']}: baseline={baseline_pred}/{baseline_correct} "
            f"promptnode={pred}/{correct}"
        )

    with open(args.output_file, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    total = len(results)
    summary = {
        "total": total,
        "solved": solved,
        "accuracy": solved / total if total else 0,
        "changed": changed,
        "fixes": fixes,
        "harms": harms,
        "cost": Cost.instance().value,
        "prompt_tokens": PromptTokens.instance().value,
        "completion_tokens": CompletionTokens.instance().value,
        "output_file": str(Path(args.output_file).resolve()),
    }
    summary_path = Path(args.output_file).with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
