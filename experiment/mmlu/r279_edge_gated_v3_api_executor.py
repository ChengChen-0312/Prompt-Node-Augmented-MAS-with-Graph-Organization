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
VALID_ACTIONS = {"KEEP_ARG", "SWITCH"}


def _strip_code_fence(text: str) -> str:
    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    return stripped


def parse_v3_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        action_match = re.search(r"(KEEP_ARG|SWITCH)", stripped, flags=re.IGNORECASE)
        label_match = re.search(r"(?:final_label|selected_label|answer|option)[\"'\s:=-]+([A-E])", stripped, flags=re.IGNORECASE)
        parsed = {
            "action": action_match.group(1).upper() if action_match else "",
            "final_label": label_match.group(1) if label_match else "",
        }
    action = str(parsed.get("action") or "").upper().strip()
    final_label = normalize_label(parsed.get("final_label") or parsed.get("selected_label"))
    independent_label = normalize_label(parsed.get("independent_label"))
    confidence = str(parsed.get("confidence") or "").lower().strip()
    edge_decision = str(parsed.get("edge_decision") or "").lower().strip()
    checks = parsed.get("evidence_checks", [])
    lifecycle = parsed.get("lifecycle_actions", [])
    if not isinstance(checks, list):
        checks = [str(checks)]
    if not isinstance(lifecycle, list):
        lifecycle = [str(lifecycle)]
    if action not in VALID_ACTIONS:
        action = "SWITCH" if final_label in VALID_LABELS and confidence == "high" else "KEEP_ARG"
    return {
        "action": action,
        "final_label": final_label if final_label in VALID_LABELS else "NONE",
        "independent_label": independent_label if independent_label in VALID_LABELS else "NONE",
        "confidence": confidence,
        "edge_decision": edge_decision,
        "evidence_checks": [str(item)[:300] for item in checks[:3]],
        "lifecycle_actions": [str(item)[:80] for item in lifecycle[:5]],
        "rationale": str(parsed.get("rationale") or "")[:1000],
        "parse_ok": bool(parsed),
    }


def apply_v3_response(record: Dict[str, Any], raw_response: str, api_executed: bool, api_error: str = "") -> Dict[str, Any]:
    output = dict(record)
    eval_only = output.get("evaluation_only", {})
    true_answer = normalize_label(eval_only.get("true_answer"))
    arg_prediction = normalize_label(eval_only.get("arg_prediction"))
    arg_is_correct = arg_prediction == true_answer if true_answer in VALID_LABELS else None

    if output.get("api_required") and api_executed and not api_error:
        parsed = parse_v3_response(raw_response)
        if parsed["action"] == "SWITCH" and parsed["final_label"] in VALID_LABELS:
            predicted = parsed["final_label"]
            fallback_reason = "api_v3_switch"
        else:
            predicted = arg_prediction
            fallback_reason = "api_v3_keep_arg"
    elif output.get("api_required"):
        parsed = {
            "action": "KEEP_ARG",
            "final_label": "NONE",
            "independent_label": "NONE",
            "confidence": "",
            "edge_decision": "",
            "evidence_checks": [],
            "lifecycle_actions": [],
            "rationale": "",
            "parse_ok": False,
        }
        predicted = arg_prediction
        fallback_reason = "api_error_fallback_arg" if api_error else "api_not_executed"
    else:
        parsed = {
            "action": "KEEP_ARG",
            "final_label": normalize_label(output.get("deterministic_selected_label")),
            "independent_label": "NONE",
            "confidence": "",
            "edge_decision": "compress",
            "evidence_checks": [],
            "lifecycle_actions": ["compress"],
            "rationale": "deterministic_arg_baseline",
            "parse_ok": True,
        }
        predicted = parsed["final_label"]
        fallback_reason = "deterministic_arg_baseline"

    is_correct = predicted == true_answer if true_answer in VALID_LABELS else None
    output.update(
        {
            "api_executed": bool(api_executed),
            "api_error": api_error,
            "raw_response": raw_response,
            "parsed_v3_response": parsed,
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
        "switches": sum(1 for row in evaluated if row.get("parsed_v3_response", {}).get("action") == "SWITCH"),
        "api_required": sum(1 for row in rows if row.get("api_required")),
        "api_executed": sum(1 for row in rows if row.get("api_executed")),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
    }


def summarize_v3_records(records: List[Dict[str, Any]], api_cost: float, prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
    evaluated = [row for row in records if row.get("is_correct") is not None]
    by_variant = {
        variant: _variant_summary([row for row in records if row.get("control_variant") == variant])
        for variant in sorted({str(row.get("control_variant")) for row in records})
    }
    correct = sum(1 for row in evaluated if row.get("is_correct"))
    return {
        "run_id": "R279",
        "title": "MMLU full24 edge-gated v3 API diagnostic",
        "claim_boundary": "Prospective full24 v3 diagnostic only; compare with R274 controls before any transfer claim.",
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
    }


async def run_async(
    records_jsonl: str = "experiment/mmlu/run_logs/mmlu_r278_edge_gated_v3_preflight_records.jsonl",
    preflight_json: str = "experiment/mmlu/res_logs/mmlu_r278_edge_gated_v3_preflight_summary.json",
    env_file: str = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env",
    output_jsonl: str = "experiment/mmlu/run_logs/mmlu_r279_edge_gated_v3_api_results.jsonl",
    summary_json: str = "experiment/mmlu/res_logs/mmlu_r279_edge_gated_v3_api_summary.json",
    report_md: str = "experiment/mmlu/run_logs/mmlu_r279_edge_gated_v3_api_report.md",
    execute_api: bool = False,
) -> Dict[str, Any]:
    preflight = load_json(preflight_json)
    if not preflight.get("preflight_pass") or not preflight.get("authorized_api_next"):
        raise RuntimeError("R278 preflight did not authorize R279.")
    if not execute_api:
        raise RuntimeError("Pass --execute_api to run R279.")
    load_env_values(env_file)
    import mas_framework.llm.gpt_chat as gpt_chat

    gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
    gpt_chat.MINE_API_KEY = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not gpt_chat.MINE_API_KEY:
        raise RuntimeError("Missing API_KEY or OPENAI_API_KEY after loading env file.")

    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    outputs: List[Dict[str, Any]] = []
    for idx, row in enumerate(load_jsonl(records_jsonl), start=1):
        if row.get("api_required"):
            try:
                response = await gpt_chat.achat(
                    model=row.get("model") or preflight.get("model") or "gpt-4o-2024-08-06",
                    msg=row.get("model_visible_messages") or [],
                    max_tokens=int(row.get("max_completion_tokens") or 128),
                    temperature=0.0,
                )
                outputs.append(apply_v3_response(row, response or "", True))
            except Exception as exc:  # pragma: no cover
                outputs.append(apply_v3_response(row, "", False, f"{type(exc).__name__}: {exc}"))
        else:
            outputs.append(apply_v3_response(row, "", False))
        if idx % 8 == 0:
            print(f"R279 progress: {idx}/{preflight.get('records')} records processed", flush=True)

    summary = summarize_v3_records(outputs, Cost.instance().value, int(PromptTokens.instance().value), int(CompletionTokens.instance().value))
    summary.update(
        {
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
        "# R279 Edge-Gated V3 API Diagnostic",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- API required/executed/errors: `{summary['api_required']}/{summary['api_executed']}/{summary['api_errors']}`",
        f"- Cost: `${summary['api_cost']:.6f}`",
        "",
        "| Variant | Correct | Accuracy | Fix/Harm | Switches |",
        "|---|---:|---:|---:|---:|",
    ]
    for variant, item in summary["by_variant"].items():
        rows.append(f"| `{variant}` | `{item['correct']}`/`{item['records']}` | `{item['accuracy']}` | `{item['fixes']}/{item['harms']}` | `{item['switches']}` |")
    rows.append("")
    return "\n".join(rows)


def run(**kwargs: Any) -> Dict[str, Any]:
    return asyncio.run(run_async(**kwargs))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute R279 edge-gated v3 full24 diagnostic.")
    parser.add_argument("--records_jsonl", default="experiment/mmlu/run_logs/mmlu_r278_edge_gated_v3_preflight_records.jsonl")
    parser.add_argument("--preflight_json", default="experiment/mmlu/res_logs/mmlu_r278_edge_gated_v3_preflight_summary.json")
    parser.add_argument("--env_file", default="/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env")
    parser.add_argument("--output_jsonl", default="experiment/mmlu/run_logs/mmlu_r279_edge_gated_v3_api_results.jsonl")
    parser.add_argument("--summary_json", default="experiment/mmlu/res_logs/mmlu_r279_edge_gated_v3_api_summary.json")
    parser.add_argument("--report_md", default="experiment/mmlu/run_logs/mmlu_r279_edge_gated_v3_api_report.md")
    parser.add_argument("--execute_api", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
