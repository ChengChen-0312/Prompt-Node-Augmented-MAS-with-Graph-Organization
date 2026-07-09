from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from experiment.mmlu.transfer_dataset import MMLUTransferDataset
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


DEFAULT_ARG_RESULTS = "experiment/mmlu/run_logs/mmlu_r292_arg_retrain_first24_api_results.jsonl"
DEFAULT_TRANSFER_JSONL = "experiment/mmlu/mmlu_stem_transfer100.jsonl"
DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r299_generic_noharm_verifier_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r299_generic_noharm_verifier_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r299_generic_noharm_verifier_report.md"

VALID_LABELS = {"A", "B", "C", "D", "E"}


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    return label[:1] if label[:1] in VALID_LABELS else "NONE"


def strip_code_fence(text: str) -> str:
    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    return stripped


def parse_verifier_response(text: str) -> Dict[str, Any]:
    stripped = strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        action_match = re.search(r"\b(KEEP_ARG|SWITCH)\b", stripped, flags=re.I)
        label_match = re.search(r"(?:selected_label|final_label|answer|option)[\"'\s:=-]+([A-E])", stripped, flags=re.I)
        parsed = {
            "action": action_match.group(1).upper() if action_match else "KEEP_ARG",
            "selected_label": label_match.group(1).upper() if label_match else "NONE",
        }
    action = str(parsed.get("action") or "").upper().strip()
    if action not in {"KEEP_ARG", "SWITCH"}:
        action = "KEEP_ARG"
    selected_label = normalize_label(parsed.get("selected_label") or parsed.get("final_label"))
    confidence = str(parsed.get("confidence") or "").lower().strip()
    return {
        "action": action,
        "selected_label": selected_label,
        "confidence": confidence,
        "trigger": str(parsed.get("trigger") or "")[:300],
        "rationale": str(parsed.get("rationale") or "")[:1200],
        "parse_ok": bool(parsed),
    }


def apply_verifier_response(row: Dict[str, Any], raw_response: str, api_error: str = "") -> Dict[str, Any]:
    out = dict(row)
    arg_prediction = normalize_label(out.get("arg_prediction") or out.get("predicted_answer"))
    true_answer = normalize_label(out.get("true_answer"))
    if api_error:
        parsed = {"action": "KEEP_ARG", "selected_label": "NONE", "confidence": "", "parse_ok": False}
        selected = arg_prediction
        reason = "api_error_keep_arg"
    else:
        parsed = parse_verifier_response(raw_response)
        if (
            parsed["action"] == "SWITCH"
            and parsed["selected_label"] in VALID_LABELS
            and parsed["confidence"] == "high"
        ):
            selected = parsed["selected_label"]
            reason = "high_confidence_switch"
        else:
            selected = arg_prediction
            reason = "keep_arg"
    out.update(
        {
            "arg_prediction": arg_prediction,
            "raw_verifier_response": raw_response,
            "parsed_verifier_response": parsed,
            "api_error": api_error,
            "predicted_answer": selected,
            "fallback_reason": reason,
            "arg_is_correct": arg_prediction == true_answer if true_answer in VALID_LABELS else None,
            "is_correct": selected == true_answer if true_answer in VALID_LABELS else None,
        }
    )
    out["fix"] = out["arg_is_correct"] is False and out["is_correct"] is True
    out["harm"] = out["arg_is_correct"] is True and out["is_correct"] is False
    return out


def build_messages(task: str, arg_prediction: str) -> List[Dict[str, str]]:
    system = (
        "You are a dataset-agnostic no-harm verifier PromptNode for multiple-choice reasoning. "
        "Your job is not to solve from scratch unless needed. Start from the current ARG answer. "
        "Switch only when the current answer is clearly invalid under the question wording, option semantics, "
        "or a domain law, and an alternative listed option is directly supported. "
        "Do not use dataset labels, row ids, memorized benchmarks, or task-specific patches. "
        "Be conservative: when uncertain, KEEP_ARG. Return only JSON."
    )
    user = (
        f"Task and options:\n{task}\n\n"
        f"Current ARG answer: {arg_prediction}\n\n"
        "Check these generic failure modes:\n"
        "- population-vs-sample or census-vs-inference mismatch\n"
        "- wording such as always/none/except/most appropriate\n"
        "- option binding mismatch between reasoning and selected label\n"
        "- simple domain law contradiction such as monotonic ratio, conservation, or definition\n\n"
        "Return JSON with keys: action KEEP_ARG or SWITCH, selected_label A-E or NONE, "
        "confidence low/medium/high, trigger, rationale. "
        "Use SWITCH only with confidence high."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def summarize(rows: List[Dict[str, Any]], api_cost: float, prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
    evaluated = [row for row in rows if row.get("is_correct") is not None]
    correct = sum(1 for row in evaluated if row.get("is_correct"))
    return {
        "run_id": "R299",
        "title": "Generic no-harm verifier PromptNode over R292 ARG predictions",
        "claim_boundary": "Teacher verifier diagnostic only; same-model API, no labels in prompts, not yet distilled ML gate.",
        "no_api": False,
        "broad_api": False,
        "records": len(rows),
        "evaluated_records": len(evaluated),
        "correct": correct,
        "accuracy": correct / len(evaluated) if evaluated else None,
        "arg_correct": sum(1 for row in evaluated if row.get("arg_is_correct")),
        "fixes": sum(1 for row in evaluated if row.get("fix")),
        "harms": sum(1 for row in evaluated if row.get("harm")),
        "switches": sum(1 for row in evaluated if row.get("fallback_reason") == "high_confidence_switch"),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
        "api_cost": round(float(api_cost), 6),
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "transfer_superiority_claim_supported": False,
        "sci_q2_ready": False,
    }


async def run_async(
    arg_results_jsonl: str = DEFAULT_ARG_RESULTS,
    transfer_jsonl: str = DEFAULT_TRANSFER_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    execute_api: bool = False,
    model: str = "gpt-4o-2024-08-06",
    limit_tasks: int | None = None,
) -> Dict[str, Any]:
    if not execute_api:
        raise RuntimeError("Pass --execute_api to run R299.")
    load_env_values(env_file)
    import mas_framework.llm.gpt_chat as gpt_chat

    gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
    gpt_chat.MINE_API_KEY = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not gpt_chat.MINE_API_KEY:
        raise RuntimeError("Missing API key after env load.")

    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    arg_rows = load_jsonl(arg_results_jsonl)
    if limit_tasks is not None:
        arg_rows = arg_rows[: int(limit_tasks)]
    dataset = MMLUTransferDataset(_repo_path(transfer_jsonl))
    by_id = {str(row.get("task_id")): row for row in dataset}

    outputs: List[Dict[str, Any]] = []
    for idx, arg_row in enumerate(arg_rows, start=1):
        task_id = str(arg_row.get("task_id"))
        data_row = by_id[task_id]
        task = dataset.record_to_input(data_row)["task"]
        base = {
            "task_id": task_id,
            "subject": arg_row.get("subject"),
            "true_answer": arg_row.get("true_answer"),
            "arg_prediction": arg_row.get("predicted_answer"),
        }
        try:
            response = await gpt_chat.achat(
                model=model,
                msg=build_messages(task, base["arg_prediction"]),
                max_tokens=220,
                temperature=0.0,
            )
            outputs.append(apply_verifier_response(base, response or "", ""))
        except Exception as exc:  # pragma: no cover
            outputs.append(apply_verifier_response(base, "", f"{type(exc).__name__}: {exc}"))
        if idx % 4 == 0:
            print(f"R299 progress: {idx}/{len(arg_rows)} tasks", flush=True)
            write_jsonl(output_jsonl, outputs)

    summary = summarize(
        outputs,
        api_cost=Cost.instance().value,
        prompt_tokens=int(PromptTokens.instance().value),
        completion_tokens=int(CompletionTokens.instance().value),
    )
    summary.update(
        {
            "arg_results_jsonl": arg_results_jsonl,
            "transfer_jsonl": transfer_jsonl,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
            "env_values_logged": False,
            "model": model,
        }
    )
    write_jsonl(output_jsonl, outputs)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R299 Generic No-Harm Verifier",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['records']}`",
            f"- Correct: `{summary['correct']}`",
            f"- Accuracy: `{summary['accuracy']}`",
            f"- ARG correct: `{summary['arg_correct']}`",
            f"- Fix/harm: `{summary['fixes']}/{summary['harms']}`",
            f"- Switches: `{summary['switches']}`",
            f"- API errors: `{summary['api_errors']}`",
            f"- Cost: `${summary['api_cost']:.6f}`",
            f"- Prompt/completion tokens: `{summary['prompt_tokens']}/{summary['completion_tokens']}`",
            "",
        ]
    )


def run(**kwargs: Any) -> Dict[str, Any]:
    return asyncio.run(run_async(**kwargs))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R299 generic no-harm verifier PromptNode.")
    parser.add_argument("--arg_results_jsonl", default=DEFAULT_ARG_RESULTS)
    parser.add_argument("--transfer_jsonl", default=DEFAULT_TRANSFER_JSONL)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--execute_api", action="store_true")
    parser.add_argument("--model", default="gpt-4o-2024-08-06")
    parser.add_argument("--limit_tasks", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
