from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r231_tiny_diagnostic_runner import load_jsonl, normalize_label
from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_json
from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


VALID_LABELS = {"A", "B", "C", "D", "E"}


def _strip_code_fence(text: str) -> str:
    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    return stripped


def parse_answer_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        label_match = re.search(
            r"(?:selected_label|answer|option)[\"'\s:=-]+([A-E])",
            stripped,
            flags=re.IGNORECASE,
        )
        parsed = {"selected_label": label_match.group(1) if label_match else ""}

    selected_label = normalize_label(parsed.get("selected_label"))
    return {
        "selected_label": selected_label if selected_label in VALID_LABELS else "NONE",
        "rationale": str(parsed.get("rationale") or "")[:1000],
        "parse_ok": bool(parsed) and selected_label in VALID_LABELS,
    }


def apply_answer_response(
    record: Dict[str, Any],
    raw_response: str,
    api_executed: bool,
    api_error: str = "",
) -> Dict[str, Any]:
    output = dict(record)
    eval_only = output.get("evaluation_only", {})
    true_answer = normalize_label(eval_only.get("true_answer"))
    arg_prediction = normalize_label(eval_only.get("arg_prediction"))
    arg_is_correct = arg_prediction == true_answer if true_answer in VALID_LABELS else None

    if output.get("api_required") and api_executed and not api_error:
        parsed = parse_answer_response(raw_response)
        predicted = parsed["selected_label"] if parsed["selected_label"] in VALID_LABELS else arg_prediction
        fallback_reason = "api_answer" if parsed["selected_label"] in VALID_LABELS else "api_parse_fallback_arg"
    elif output.get("api_required"):
        parsed = {"selected_label": "NONE", "rationale": "", "parse_ok": False}
        predicted = arg_prediction
        fallback_reason = "api_error_fallback_arg" if api_error else "api_not_executed"
    else:
        parsed = {
            "selected_label": normalize_label(output.get("deterministic_selected_label")),
            "rationale": "deterministic_control",
            "parse_ok": True,
        }
        predicted = parsed["selected_label"]
        fallback_reason = "deterministic_control"

    is_correct = predicted == true_answer if true_answer in VALID_LABELS else None
    output.update(
        {
            "api_executed": bool(api_executed),
            "api_error": api_error,
            "raw_response": raw_response,
            "parsed_answer_response": parsed,
            "predicted_answer": predicted,
            "true_answer": true_answer,
            "arg_prediction": arg_prediction,
            "arg_is_correct": arg_is_correct,
            "is_correct": is_correct,
            "fix": arg_is_correct is False and is_correct is True,
            "harm": arg_is_correct is True and is_correct is False,
            "fallback_reason": fallback_reason,
        }
    )
    return output


def _variant_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    evaluated = [row for row in rows if row.get("is_correct") is not None]
    correct = sum(1 for row in evaluated if row.get("is_correct"))
    return {
        "records": len(rows),
        "evaluated_records": len(evaluated),
        "correct": correct,
        "accuracy": correct / len(evaluated) if evaluated else None,
        "fixes": sum(1 for row in evaluated if row.get("fix")),
        "harms": sum(1 for row in evaluated if row.get("harm")),
        "api_required": sum(1 for row in rows if row.get("api_required")),
        "api_executed": sum(1 for row in rows if row.get("api_executed")),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
    }


def summarize_executed_records(
    records: List[Dict[str, Any]],
    api_cost: float,
    prompt_tokens: int,
    completion_tokens: int,
) -> Dict[str, Any]:
    evaluated = [row for row in records if row.get("is_correct") is not None]
    by_variant = {
        variant: _variant_summary([row for row in records if row.get("control_variant") == variant])
        for variant in sorted({str(row.get("control_variant")) for row in records})
    }
    by_selection_role = {
        role: _variant_summary([row for row in records if row.get("selection_role") == role])
        for role in sorted({str(row.get("selection_role")) for row in records})
    }
    correct = sum(1 for row in evaluated if row.get("is_correct"))
    return {
        "records": len(records),
        "evaluated_records": len(evaluated),
        "correct": correct,
        "accuracy": correct / len(evaluated) if evaluated else None,
        "fixes": sum(1 for row in evaluated if row.get("fix")),
        "harms": sum(1 for row in evaluated if row.get("harm")),
        "api_required": sum(1 for row in records if row.get("api_required")),
        "api_executed": sum(1 for row in records if row.get("api_executed")),
        "api_errors": sum(1 for row in records if row.get("api_error")),
        "api_cost": round(float(api_cost), 6),
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in records).items())),
        "by_variant": by_variant,
        "by_selection_role": by_selection_role,
    }


async def execute_transfer_diagnostic(
    records_jsonl: str,
    preflight_json: str,
    env_file: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
    execute_api: bool,
) -> Dict[str, Any]:
    preflight = load_json(preflight_json)
    if not preflight.get("preflight_pass") or not preflight.get("authorized_api_next"):
        raise RuntimeError("R252 preflight did not authorize the tiny transfer diagnostic.")
    if not execute_api:
        raise RuntimeError("Pass --execute_api to run R253; dry-run belongs to R252.")

    load_env_values(env_file)
    import mas_framework.llm.gpt_chat as gpt_chat

    gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
    gpt_chat.MINE_API_KEY = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not gpt_chat.MINE_API_KEY:
        raise RuntimeError("Missing API_KEY or OPENAI_API_KEY after loading env file.")

    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    input_records = load_jsonl(records_jsonl)
    outputs: List[Dict[str, Any]] = []
    for idx, row in enumerate(input_records, start=1):
        if row.get("api_required"):
            try:
                response = await gpt_chat.achat(
                    model=row.get("model") or preflight.get("model") or "gpt-4o-2024-08-06",
                    msg=row.get("model_visible_messages") or [],
                    max_tokens=int(row.get("max_completion_tokens") or 64),
                    temperature=0.0,
                )
                outputs.append(apply_answer_response(row, response or "", api_executed=True))
            except Exception as exc:  # pragma: no cover - exercised only with API/backend failure.
                outputs.append(
                    apply_answer_response(
                        row,
                        "",
                        api_executed=False,
                        api_error=f"{type(exc).__name__}: {exc}",
                    )
                )
        else:
            outputs.append(apply_answer_response(row, "", api_executed=False))
        if idx % 10 == 0:
            print(f"R253 progress: {idx}/{len(input_records)} records processed", flush=True)

    summary = summarize_executed_records(
        outputs,
        api_cost=Cost.instance().value,
        prompt_tokens=int(PromptTokens.instance().value),
        completion_tokens=int(CompletionTokens.instance().value),
    )
    summary.update(
        {
            "run_id": "R253",
            "title": "MMLU tiny transfer API diagnostic",
            "claim_boundary": "Tiny same-model transfer diagnostic only; not a broad held-out result, transfer proof, or SCI-Q2 readiness claim.",
            "model": preflight.get("model", "gpt-4o-2024-08-06"),
            "records_jsonl": records_jsonl,
            "preflight_json": preflight_json,
            "output_jsonl": output_jsonl,
            "env_file": env_file,
            "env_values_logged": False,
            "no_api": False,
            "broad_api": False,
        }
    )

    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for row in outputs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R253 MMLU Tiny Transfer API Diagnostic",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Records: `{summary['records']}`",
        f"- Evaluated records: `{summary['evaluated_records']}`",
        f"- API required/executed/errors: `{summary['api_required']}/{summary['api_executed']}/{summary['api_errors']}`",
        f"- Correct: `{summary['correct']}`",
        f"- Accuracy: `{summary['accuracy']}`",
        f"- Fixes/harms vs ARG baseline: `{summary['fixes']}` / `{summary['harms']}`",
        f"- Cost: `${summary['api_cost']:.6f}`",
        f"- Prompt/completion tokens: `{summary['prompt_tokens']}/{summary['completion_tokens']}`",
        "",
        "## By Variant",
        "",
        "| Variant | Records | Correct | Accuracy | Fix/Harm | API executed/errors |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for variant, item in summary["by_variant"].items():
        rows.append(
            f"| `{variant}` | `{item['records']}` | `{item['correct']}` | `{item['accuracy']}` | `{item['fixes']}/{item['harms']}` | `{item['api_executed']}/{item['api_errors']}` |"
        )
    rows.extend(
        [
            "",
            "## Boundary",
            "",
            "This diagnostic uses the R252 preflighted tiny16 set only. It can motivate the next transfer experiment, but by itself it is not a SCI-Q2 result claim.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute R253 MMLU tiny transfer API diagnostic.")
    parser.add_argument("--records_jsonl", required=True)
    parser.add_argument("--preflight_json", required=True)
    parser.add_argument("--env_file", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--execute_api", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = asyncio.run(
        execute_transfer_diagnostic(
            records_jsonl=args.records_jsonl,
            preflight_json=args.preflight_json,
            env_file=args.env_file,
            output_jsonl=args.output_jsonl,
            summary_json=args.summary_json,
            report_md=args.report_md,
            execute_api=args.execute_api,
        )
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
