from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r334_prospective_selector_eval_manifest.jsonl"
DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r335_prospective_selector_eval_api_smoke_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r335_prospective_selector_eval_api_smoke_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r335_prospective_selector_eval_api_smoke_report.md"

VALID_LABELS = {"A", "B", "C", "D", "E"}
FORBIDDEN_PROMPT_FIELDS = {"task_id", "true_answer", "gold_answer", "is_correct", "evaluation_only", "source_ref_hash"}


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    p = _repo_path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _label(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text[:1] if text[:1] in VALID_LABELS else ""


def _strip_code_fence(text: str) -> str:
    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    return stripped


def parse_plain_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        match = re.search(r"(?:selected_label|final_label|answer|option)[\"'\s:=-]+([A-E])", stripped, flags=re.I)
        parsed = {"selected_label": match.group(1) if match else ""}
    return {
        "selected_label": _label(parsed.get("selected_label") or parsed.get("final_label")),
        "confidence": str(parsed.get("confidence") or "").lower(),
        "rationale": str(parsed.get("rationale") or "")[:800],
        "parse_ok": bool(parsed),
    }


def parse_selector_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        action = re.search(r"\b(KEEP_ARG|SWITCH)\b", stripped, flags=re.I)
        label = re.search(r"(?:final_label|selected_label|answer|option)[\"'\s:=-]+([A-E])", stripped, flags=re.I)
        conf = re.search(r"confidence[\"'\s:=-]+([A-Za-z0-9_.]+)", stripped, flags=re.I)
        parsed = {
            "action": action.group(1).upper() if action else "KEEP_ARG",
            "final_label": label.group(1) if label else "",
            "confidence": conf.group(1) if conf else "",
        }
    action = str(parsed.get("action") or "KEEP_ARG").strip().upper()
    if action not in {"KEEP_ARG", "SWITCH"}:
        action = "KEEP_ARG"
    return {
        "action": action,
        "final_label": _label(parsed.get("final_label") or parsed.get("selected_label")),
        "confidence": str(parsed.get("confidence") or "").lower(),
        "rationale": str(parsed.get("rationale") or "")[:800],
        "parse_ok": bool(parsed),
    }


def _high_confidence(confidence: str) -> bool:
    text = str(confidence or "").strip().lower()
    if text in {"high", "very_high", "high_confidence"}:
        return True
    try:
        return float(text) >= 0.85
    except ValueError:
        return False


def _selected_records(manifest_jsonl: str, limit_tasks: int) -> List[Dict[str, Any]]:
    rows = _load_jsonl(manifest_jsonl)
    task_order: List[str] = []
    for row in rows:
        task_id = str(row.get("task_id") or "")
        if task_id and task_id not in task_order:
            task_order.append(task_id)
        if len(task_order) >= limit_tasks:
            break
    selected = set(task_order[:limit_tasks])
    return [row for row in rows if row.get("task_id") in selected]


def _leakage(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    violations = []
    for row in rows:
        prompt = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", [])).lower()
        for field in FORBIDDEN_PROMPT_FIELDS:
            if field in prompt:
                violations.append({"task_id": row.get("task_id", ""), "variant": row.get("control_variant", ""), "field": field})
    return violations


def build_api_smoke_plan(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL, limit_tasks: int = 6) -> Dict[str, Any]:
    rows = _selected_records(manifest_jsonl, limit_tasks)
    violations = _leakage(rows)
    tasks = sorted({row.get("task_id") for row in rows})
    return {
        "run_id": "R335",
        "title": "Prospective selector eval API smoke",
        "claim_boundary": "R335 is a bounded API smoke only. It cannot support a paper claim by itself.",
        "no_api": True,
        "broad_api": False,
        "tasks": len(tasks),
        "records": len(rows),
        "api_calls_planned": len(rows),
        "runtime_baseline_injection_required": True,
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_executed": False,
        "sci_q2_ready": False,
        "next_required_run": "R335_execute_with_api_or_R336_analyze_if_executed",
    }


def _inject_baseline(messages: List[Dict[str, str]], baseline: str) -> List[Dict[str, str]]:
    injected = []
    for message in messages:
        if message.get("role") == "user":
            content = str(message.get("content") or "")
            content = content.replace(
                "PromptNode identities:",
                f"ARG initial choice from baseline: {baseline}\n\nPromptNode identities:",
            )
            injected.append({**message, "content": content})
        else:
            injected.append(dict(message))
    return injected


async def _call(messages: List[Dict[str, str]], model: str, max_tokens: int) -> str:
    import mas_framework.llm.gpt_chat as gpt_chat

    return await gpt_chat.achat(model=model, msg=messages, max_tokens=max_tokens, temperature=0.0) or ""


def _score_row(row: Dict[str, Any], predicted: str, baseline: str, raw: str, parsed: Dict[str, Any], api_error: str = "") -> Dict[str, Any]:
    true_answer = _label((row.get("evaluation_only") or {}).get("true_answer"))
    baseline_correct = baseline == true_answer if true_answer else None
    is_correct = predicted == true_answer if true_answer else None
    out = dict(row)
    out.update(
        {
            "api_executed": not bool(api_error),
            "api_error": api_error,
            "raw_response": raw,
            "parsed_response": parsed,
            "baseline_prediction": baseline,
            "predicted_answer": predicted,
            "true_answer": true_answer,
            "baseline_is_correct": baseline_correct,
            "is_correct": is_correct,
            "fix": baseline_correct is False and is_correct is True,
            "harm": baseline_correct is True and is_correct is False,
        }
    )
    return out


async def execute_api_smoke(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    limit_tasks: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _selected_records(manifest_jsonl, limit_tasks)
    violations = _leakage(rows)
    if violations:
        raise RuntimeError(f"Leakage violations block API smoke: {violations}")
    load_env_values(env_file)
    import mas_framework.llm.gpt_chat as gpt_chat

    gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
    gpt_chat.MINE_API_KEY = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not gpt_chat.MINE_API_KEY:
        raise RuntimeError("Missing API_KEY or OPENAI_API_KEY after loading env file.")

    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    by_task: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for row in rows:
        by_task.setdefault(str(row["task_id"]), {})[str(row["control_variant"])] = row
    outputs: List[Dict[str, Any]] = []
    for task_id, variants in by_task.items():
        baseline_row = variants["arg_baseline_direct"]
        try:
            baseline_raw = await _call(
                baseline_row["model_visible_messages"],
                baseline_row.get("model") or "gpt-4o-2024-08-06",
                int(baseline_row.get("max_completion_tokens") or 160),
            )
            baseline_parsed = parse_plain_response(baseline_raw)
            baseline = baseline_parsed["selected_label"] or "A"
            outputs.append(_score_row(baseline_row, baseline, baseline, baseline_raw, baseline_parsed))
        except Exception as exc:
            baseline = "A"
            outputs.append(_score_row(baseline_row, baseline, baseline, "", {"parse_ok": False}, f"{type(exc).__name__}: {exc}"))
        for variant in ["cost_matched_plain_requery", "selector_promptnode_promptedge_policy"]:
            row = variants[variant]
            try:
                messages = row["model_visible_messages"]
                if variant == "selector_promptnode_promptedge_policy":
                    messages = _inject_baseline(messages, baseline)
                raw = await _call(messages, row.get("model") or "gpt-4o-2024-08-06", int(row.get("max_completion_tokens") or 160))
                if variant == "selector_promptnode_promptedge_policy":
                    parsed = parse_selector_response(raw)
                    predicted = (
                        parsed["final_label"]
                        if parsed["action"] == "SWITCH" and parsed["final_label"] and _high_confidence(parsed["confidence"])
                        else baseline
                    )
                else:
                    parsed = parse_plain_response(raw)
                    predicted = parsed["selected_label"] or baseline
                outputs.append(_score_row(row, predicted, baseline, raw, parsed))
            except Exception as exc:
                outputs.append(_score_row(row, baseline, baseline, "", {"parse_ok": False}, f"{type(exc).__name__}: {exc}"))
    return outputs, summarize_outputs(outputs)


def summarize_outputs(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_variant: Dict[str, Dict[str, Any]] = {}
    for variant in sorted({row["control_variant"] for row in records}):
        rows = [row for row in records if row["control_variant"] == variant]
        ok = [row for row in rows if row.get("is_correct") is not None and not row.get("api_error")]
        by_variant[variant] = {
            "records": len(rows),
            "evaluated_records": len(ok),
            "correct": sum(1 for row in ok if row["is_correct"]),
            "accuracy": sum(1 for row in ok if row["is_correct"]) / len(ok) if ok else None,
            "fixes": sum(1 for row in ok if row.get("fix")),
            "harms": sum(1 for row in ok if row.get("harm")),
        }
    return {
        "run_id": "R335",
        "title": "Prospective selector eval API smoke",
        "claim_boundary": "R335 is a bounded API smoke only. It cannot support a paper claim by itself.",
        "no_api": False,
        "broad_api": False,
        "tasks": len({row["task_id"] for row in records}),
        "records": len(records),
        "api_calls_planned": len(records),
        "api_executed": sum(1 for row in records if row.get("api_executed")),
        "api_errors": sum(1 for row in records if row.get("api_error")),
        "api_cost": round(float(Cost.instance().value), 6),
        "prompt_tokens": int(PromptTokens.instance().value),
        "completion_tokens": int(CompletionTokens.instance().value),
        "variant_counts": dict(sorted(Counter(row["control_variant"] for row in records).items())),
        "by_variant": by_variant,
        "sci_q2_ready": False,
        "next_required_run": "R336_prospective_selector_eval_smoke_analysis",
    }


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# R335 Prospective Selector Eval API Smoke",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Tasks: `{summary['tasks']}`",
        f"- Records/API calls: `{summary['records']}`",
        f"- API executed: `{summary['api_executed']}`",
    ]
    if summary.get("by_variant"):
        lines.extend(["", "## By Variant", "", "| Variant | Correct | Records | Accuracy | Fixes | Harms |", "|---|---:|---:|---:|---:|---:|"])
        for variant, item in summary["by_variant"].items():
            lines.append(
                f"| `{variant}` | `{item['correct']}` | `{item['evaluated_records']}` | `{item['accuracy']}` | `{item['fixes']}` | `{item['harms']}` |"
            )
    lines.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(lines)


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    limit_tasks: int = 6,
    execute_api: bool = False,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    if execute_api:
        records, summary = asyncio.run(execute_api_smoke(manifest_jsonl=manifest_jsonl, env_file=env_file, limit_tasks=limit_tasks))
        _write_jsonl(output_jsonl, records)
    else:
        summary = build_api_smoke_plan(manifest_jsonl=manifest_jsonl, limit_tasks=limit_tasks)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R335 prospective selector API smoke.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--limit_tasks", type=int, default=6)
    parser.add_argument("--execute_api", action="store_true")
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
