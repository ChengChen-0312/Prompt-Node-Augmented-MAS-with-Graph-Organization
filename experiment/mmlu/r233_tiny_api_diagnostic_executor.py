from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r232_tiny_diagnostic_preflight_audit import load_json, load_jsonl
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


VALID_LABELS = {"A", "B", "C", "D", "E"}
VALID_ACTIONS = {"switch_to_objective", "abstain"}


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label.startswith("NONE"):
        return "NONE"
    return label[:1] if label[:1] in VALID_LABELS else "NONE"


def _strip_code_fence(text: str) -> str:
    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    return stripped


def parse_router_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        action_match = re.search(r"action[\"'\s:=-]+([A-Za-z_]+)", stripped, flags=re.IGNORECASE)
        label_match = re.search(r"selected_label[\"'\s:=-]+([A-E]|NONE)", stripped, flags=re.IGNORECASE)
        parsed = {
            "action": action_match.group(1) if action_match else "",
            "selected_label": label_match.group(1) if label_match else "NONE",
        }
    action = str(parsed.get("action") or "").strip()
    selected_label = normalize_label(parsed.get("selected_label"))
    if action not in VALID_ACTIONS:
        action = "abstain"
    return {
        "action": action,
        "selected_label": selected_label,
        "rationale": str(parsed.get("rationale") or "")[:1000],
        "parse_ok": bool(parsed),
    }


def apply_router_response(
    record: Dict[str, Any],
    raw_response: str,
    api_executed: bool,
    api_error: str = "",
) -> Dict[str, Any]:
    output = dict(record)
    baseline = normalize_label(output.get("baseline_prediction"))
    true_answer = normalize_label(output.get("true_answer"))
    baseline_is_correct = baseline == true_answer if true_answer in VALID_LABELS else None

    if output.get("api_required") and api_executed and not api_error:
        parsed = parse_router_response(raw_response)
        if parsed["action"] == "switch_to_objective" and parsed["selected_label"] in VALID_LABELS:
            predicted = parsed["selected_label"]
            fallback_reason = "api_router_switch"
        else:
            predicted = baseline
            fallback_reason = "api_router_abstain"
    elif output.get("api_required"):
        parsed = {"action": "error_fallback", "selected_label": "NONE", "rationale": "", "parse_ok": False}
        predicted = baseline
        fallback_reason = "api_error_fallback" if api_error else "api_not_executed"
    else:
        parsed = {
            "action": output.get("planned_action"),
            "selected_label": output.get("planned_selected_label"),
            "rationale": "deterministic_control",
            "parse_ok": True,
        }
        predicted = normalize_label(output.get("planned_selected_label"))
        fallback_reason = "deterministic_control"

    is_correct = predicted == true_answer if true_answer in VALID_LABELS else None
    output.update(
        {
            "api_executed": bool(api_executed),
            "api_error": api_error,
            "raw_response": raw_response,
            "parsed_router_response": parsed,
            "predicted_answer": predicted,
            "fallback_reason": fallback_reason,
            "baseline_is_correct": baseline_is_correct,
            "is_correct": is_correct,
            "fix": baseline_is_correct is False and is_correct is True,
            "harm": baseline_is_correct is True and is_correct is False,
        }
    )
    return output


def summarize_executed_records(
    records: List[Dict[str, Any]],
    api_cost: float,
    prompt_tokens: int,
    completion_tokens: int,
) -> Dict[str, Any]:
    evaluated = [row for row in records if row.get("is_correct") is not None and not row.get("api_error")]
    by_variant: Dict[str, Dict[str, Any]] = {}
    for variant in sorted({str(row.get("control_variant")) for row in records}):
        rows = [row for row in records if str(row.get("control_variant")) == variant and not row.get("api_error")]
        evaluated_rows = [row for row in rows if row.get("is_correct") is not None]
        by_variant[variant] = {
            "records": len(rows),
            "correct": sum(1 for row in evaluated_rows if row.get("is_correct")),
            "accuracy": (
                sum(1 for row in evaluated_rows if row.get("is_correct")) / len(evaluated_rows)
                if evaluated_rows
                else None
            ),
            "fixes": sum(1 for row in evaluated_rows if row.get("fix")),
            "harms": sum(1 for row in evaluated_rows if row.get("harm")),
            "api_required": sum(1 for row in rows if row.get("api_required")),
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
    }


def load_env_values(env_file: str) -> None:
    if not env_file:
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key:
                os.environ[key] = value


async def execute_tiny_diagnostic(
    records_jsonl: str,
    preflight_json: str,
    env_file: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
    execute_api: bool,
    run_id: str = "R233",
) -> Dict[str, Any]:
    preflight = load_json(preflight_json)
    if preflight.get("api_status") != "authorized_tiny_diagnostic" or not preflight.get("preflight_pass"):
        raise RuntimeError("R232 preflight did not authorize the tiny diagnostic.")
    if not execute_api:
        raise RuntimeError("Pass --execute_api to run R233; dry-run belongs to R231/R232.")

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
    for row in input_records:
        if row.get("api_required"):
            try:
                response = await gpt_chat.achat(
                    model=row.get("model") or "gpt-4o-2024-08-06",
                    msg=row.get("model_visible_messages") or [],
                    max_tokens=int(row.get("max_completion_tokens") or 48),
                    temperature=0.0,
                )
                outputs.append(apply_router_response(row, response or "", api_executed=True))
            except Exception as exc:  # pragma: no cover - exercised only on API failure.
                outputs.append(
                    apply_router_response(
                        row,
                        "",
                        api_executed=False,
                        api_error=f"{type(exc).__name__}: {exc}",
                    )
                )
        else:
            outputs.append(apply_router_response(row, "", api_executed=False))

    summary = summarize_executed_records(
        outputs,
        api_cost=Cost.instance().value,
        prompt_tokens=int(PromptTokens.instance().value),
        completion_tokens=int(CompletionTokens.instance().value),
    )
    summary.update(
        {
            "run_id": run_id,
            "title": "Tiny API diagnostic executor",
            "claim_boundary": "Tiny pre-registered diagnostic only; not a paper-level accuracy or SCI-Q2 readiness claim.",
            "model": "gpt-4o-2024-08-06",
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
        "# R233 Tiny API Diagnostic",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Result",
        "",
        f"- Records: `{summary['records']}`",
        f"- Evaluated records: `{summary['evaluated_records']}`",
        f"- API required/executed/errors: `{summary['api_required']}/{summary['api_executed']}/{summary['api_errors']}`",
        f"- Correct: `{summary['correct']}`",
        f"- Accuracy: `{summary['accuracy']}`",
        f"- Fixes/harms: `{summary['fixes']}/{summary['harms']}`",
        f"- Cost: `${summary['api_cost']:.6f}`",
        f"- Prompt/completion tokens: `{summary['prompt_tokens']}/{summary['completion_tokens']}`",
        "",
        "## By Variant",
        "",
        "| Variant | Records | Correct | Accuracy | Fix/Harm | API required |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for variant, item in summary["by_variant"].items():
        rows.append(
            f"| `{variant}` | `{item['records']}` | `{item['correct']}` | `{item['accuracy']}` | `{item['fixes']}/{item['harms']}` | `{item['api_required']}` |"
        )
    rows.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a tiny diagnostic over the R232-authorized records only. It is not a broad held-out result.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute R233 tiny router-final API diagnostic.")
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
        execute_tiny_diagnostic(
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
