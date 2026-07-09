from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from experiment.mmlu.r335_prospective_selector_eval_api_smoke import DEFAULT_ENV_FILE, _label, _strip_code_fence, parse_plain_response
from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import _leakage
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r423_mmlu_stem_cost_probe_manifest.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r424_mmlu_stem_cost_probe_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r424_mmlu_stem_cost_probe_api_execution_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r424_mmlu_stem_cost_probe_api_execution_report.md"


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


def parse_promptnode_probe_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        label = re.search(r"(?:candidate_label|selected_label|answer|option)[\"'\s:=-]+([A-E])", stripped, flags=re.I)
        parsed = {"candidate_label": label.group(1) if label else "", "rationale": stripped[:800]}
    return {
        "candidate_label": _label(parsed.get("candidate_label") or parsed.get("selected_label")),
        "confidence": parsed.get("confidence", ""),
        "evidence_count": int(float(parsed.get("evidence_count") or 0)) if str(parsed.get("evidence_count") or "").replace(".", "", 1).isdigit() else 0,
        "promptnode_roles": parsed.get("promptnode_roles") if isinstance(parsed.get("promptnode_roles"), list) else [],
        "promptedge_permissions": parsed.get("promptedge_permissions") if isinstance(parsed.get("promptedge_permissions"), list) else [],
        "lifecycle_actions": parsed.get("lifecycle_actions") if isinstance(parsed.get("lifecycle_actions"), list) else [],
        "rationale": str(parsed.get("rationale") or "")[:800],
        "parse_ok": bool(parsed),
    }


async def _call(row: Dict[str, Any]) -> Tuple[str, float, int, int]:
    import mas_framework.llm.gpt_chat as gpt_chat

    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()
    raw = await gpt_chat.achat(
        model=row.get("model") or "gpt-4o-2024-08-06",
        msg=row.get("model_visible_messages") or [],
        max_tokens=int(row.get("max_completion_tokens") or 220),
        temperature=0.0,
    ) or ""
    return raw, float(Cost.instance().value), int(PromptTokens.instance().value), int(CompletionTokens.instance().value)


def build_api_execution_plan(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    tasks = sorted({row.get("task_id") for row in rows})
    return {
        "run_id": "R424",
        "title": "MMLU STEM cost probe API execution",
        "claim_boundary": "R424 executes the R423 cost probe only when --execute_api is passed. It measures cost only.",
        "no_api": True,
        "broad_api": False,
        "tasks": len(tasks),
        "api_calls_planned": len(rows),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_executed": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R424_execute_with_api_or_R425_analyze_cost_probe",
    }


async def execute_api(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL, env_file: str = DEFAULT_ENV_FILE) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    if violations:
        raise RuntimeError(f"Leakage violations block API execution: {violations}")
    load_env_values(env_file)
    import mas_framework.llm.gpt_chat as gpt_chat

    gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
    gpt_chat.MINE_API_KEY = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not gpt_chat.MINE_API_KEY:
        raise RuntimeError("Missing API_KEY or OPENAI_API_KEY after loading env file.")

    outputs: List[Dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        try:
            raw, cost, prompt_tokens, completion_tokens = await _call(row)
            if row.get("control_variant") == "arg_direct_cost_probe":
                parsed = parse_plain_response(raw)
                predicted = parsed["selected_label"]
            else:
                parsed = parse_promptnode_probe_response(raw)
                predicted = parsed["candidate_label"]
            true_answer = _label((row.get("evaluation_only") or {}).get("true_answer"))
            out.update(
                {
                    "api_executed": True,
                    "api_error": "",
                    "raw_response": raw,
                    "parsed_response": parsed,
                    "predicted_answer": predicted,
                    "true_answer": true_answer,
                    "is_correct": predicted == true_answer if true_answer else None,
                    "api_cost": round(cost, 6),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                }
            )
        except Exception as exc:
            out.update(
                {
                    "api_executed": False,
                    "api_error": f"{type(exc).__name__}: {exc}",
                    "raw_response": "",
                    "parsed_response": {},
                    "predicted_answer": "",
                    "api_cost": 0.0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                }
            )
        outputs.append(out)
    return outputs, _summarize(outputs)


def _summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_variant: Dict[str, Dict[str, Any]] = {}
    for variant, values in defaultdict(list, {}).items():
        pass
    variants = sorted({str(row.get("control_variant")) for row in rows})
    for variant in variants:
        vals = [row for row in rows if row.get("control_variant") == variant]
        by_variant[variant] = {
            "records": len(vals),
            "api_executed": sum(1 for row in vals if row.get("api_executed")),
            "api_errors": sum(1 for row in vals if row.get("api_error")),
            "correct": sum(1 for row in vals if row.get("is_correct")),
            "api_cost": round(sum(float(row.get("api_cost") or 0.0) for row in vals), 6),
            "prompt_tokens": sum(int(row.get("prompt_tokens") or 0) for row in vals),
            "completion_tokens": sum(int(row.get("completion_tokens") or 0) for row in vals),
        }
        by_variant[variant]["cost_per_task"] = round(by_variant[variant]["api_cost"] / len(vals), 6) if vals else None
    return {
        "run_id": "R424",
        "title": "MMLU STEM cost probe API execution",
        "claim_boundary": "R424 measures per-call cost for a small STEM probe. Accuracy is diagnostic only.",
        "no_api": False,
        "broad_api": False,
        "tasks": len({row.get("task_id") for row in rows}),
        "api_executed": sum(1 for row in rows if row.get("api_executed")),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
        "api_cost": round(sum(float(row.get("api_cost") or 0.0) for row in rows), 6),
        "prompt_tokens": sum(int(row.get("prompt_tokens") or 0) for row in rows),
        "completion_tokens": sum(int(row.get("completion_tokens") or 0) for row in rows),
        "by_variant": by_variant,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R425_analyze_mmlu_stem_cost_probe",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R424 MMLU STEM Cost Probe API Execution",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- API executed/errors: `{summary.get('api_executed', 0)}/{summary.get('api_errors', 0)}`",
            f"- API cost: `{summary.get('api_cost', '-')}`",
            f"- Tokens prompt/completion: `{summary.get('prompt_tokens', '-')}/{summary.get('completion_tokens', '-')}`",
            f"- By variant: `{summary.get('by_variant', {})}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    execute_api_flag: bool = False,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    if execute_api_flag:
        rows, summary = asyncio.run(execute_api(manifest_jsonl=manifest_jsonl, env_file=env_file))
        _write_jsonl(output_jsonl, rows)
    else:
        summary = build_api_execution_plan(manifest_jsonl=manifest_jsonl)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R424 MMLU STEM cost probe API execution.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--execute_api", action="store_true")
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    kwargs = vars(args)
    kwargs["execute_api_flag"] = kwargs.pop("execute_api")
    print(json.dumps(run(**kwargs), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
