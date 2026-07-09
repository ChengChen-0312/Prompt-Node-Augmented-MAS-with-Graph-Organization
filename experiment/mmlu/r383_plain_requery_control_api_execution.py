from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from experiment.mmlu.r335_prospective_selector_eval_api_smoke import DEFAULT_ENV_FILE, _label, parse_plain_response
from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import _leakage
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r382_plain_requery_control_manifest.jsonl"
DEFAULT_R380_RESULTS = "experiment/mmlu/run_logs/mmlu_r380_option_binding_fresh_eval_api_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r383_plain_requery_control_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r383_plain_requery_control_api_execution_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r383_plain_requery_control_api_execution_report.md"


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


async def _call(row: Dict[str, Any]) -> str:
    import mas_framework.llm.gpt_chat as gpt_chat

    return await gpt_chat.achat(
        model=row.get("model") or "gpt-4o-2024-08-06",
        msg=row.get("model_visible_messages") or [],
        max_tokens=int(row.get("max_completion_tokens") or 220),
        temperature=0.0,
    ) or ""


def build_api_execution_plan(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    tasks = sorted({row.get("task_id") for row in rows})
    return {
        "run_id": "R383",
        "title": "Plain requery control API execution",
        "claim_boundary": "R383 executes the R382 same-task plain requery control only when --execute_api is passed.",
        "no_api": True,
        "broad_api": False,
        "tasks": len(tasks),
        "api_calls_planned": len(rows),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_executed": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R383_execute_with_api_or_R384_analyze_if_executed",
    }


async def execute_api(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    r380_results: str = DEFAULT_R380_RESULTS,
    env_file: str = DEFAULT_ENV_FILE,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    if violations:
        raise RuntimeError(f"Leakage violations block API execution: {violations}")
    r380_by_task = {row.get("task_id"): row for row in _load_jsonl(r380_results)}
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
    for row in rows:
        out = dict(row)
        reference = r380_by_task.get(row.get("task_id"), {})
        true_answer = _label((row.get("evaluation_only") or {}).get("true_answer"))
        try:
            raw = await _call(row)
            parsed = parse_plain_response(raw)
            prediction = _label(parsed.get("selected_label"))
            out.update(
                {
                    "api_executed": True,
                    "api_error": "",
                    "raw_response": raw,
                    "parsed_response": parsed,
                    "true_answer": true_answer,
                    "plain_prediction": prediction,
                    "plain_correct": prediction == true_answer,
                }
            )
        except Exception as exc:
            out.update(
                {
                    "api_executed": False,
                    "api_error": f"{type(exc).__name__}: {exc}",
                    "raw_response": "",
                    "parsed_response": {},
                    "true_answer": true_answer,
                    "plain_prediction": "",
                    "plain_correct": False,
                }
            )
        out.update(
            {
                "r380_arg_prediction": reference.get("arg_prediction"),
                "r380_arg_correct": reference.get("arg_correct"),
                "r380_option_binding_prediction": reference.get("final_prediction"),
                "r380_option_binding_correct": reference.get("final_correct"),
            }
        )
        outputs.append(out)
    return outputs, _summarize(outputs)


def _summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    arg_correct = sum(1 for row in rows if row.get("r380_arg_correct"))
    plain_correct = sum(1 for row in rows if row.get("plain_correct"))
    option_binding_correct = sum(1 for row in rows if row.get("r380_option_binding_correct"))
    return {
        "run_id": "R383",
        "title": "Plain requery control API execution",
        "claim_boundary": "R383 is a same-task control for R380. It requires R384 analysis before deciding whether the graph claim survives the control.",
        "no_api": False,
        "broad_api": False,
        "tasks": len(rows),
        "api_executed": sum(1 for row in rows if row.get("api_executed")),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
        "arg_correct": arg_correct,
        "plain_requery_correct": plain_correct,
        "option_binding_correct": option_binding_correct,
        "plain_delta_vs_arg": plain_correct - arg_correct,
        "option_binding_delta_vs_plain": option_binding_correct - plain_correct,
        "plain_fix_task_ids": [
            row.get("task_id") for row in rows if not row.get("r380_arg_correct") and row.get("plain_correct")
        ],
        "option_binding_only_fix_task_ids": [
            row.get("task_id")
            for row in rows
            if row.get("r380_option_binding_correct") and not row.get("plain_correct")
        ],
        "plain_only_fix_task_ids": [
            row.get("task_id")
            for row in rows
            if row.get("plain_correct") and not row.get("r380_option_binding_correct")
        ],
        "api_cost": round(float(Cost.instance().value), 6),
        "prompt_tokens": int(PromptTokens.instance().value),
        "completion_tokens": int(CompletionTokens.instance().value),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R384_plain_requery_control_analysis",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R383 Plain Requery Control API Execution",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- API executed/errors: `{summary.get('api_executed', 0)}/{summary.get('api_errors', 0)}`",
            f"- ARG/plain/OptionBinding correct: `{summary.get('arg_correct', '-')}/{summary.get('plain_requery_correct', '-')}/{summary.get('option_binding_correct', '-')}`",
            f"- Plain delta vs ARG: `{summary.get('plain_delta_vs_arg', '-')}`",
            f"- OptionBinding delta vs plain: `{summary.get('option_binding_delta_vs_plain', '-')}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    r380_results: str = DEFAULT_R380_RESULTS,
    env_file: str = DEFAULT_ENV_FILE,
    execute_api_flag: bool = False,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    if execute_api_flag:
        rows, summary = asyncio.run(execute_api(manifest_jsonl=manifest_jsonl, r380_results=r380_results, env_file=env_file))
        _write_jsonl(output_jsonl, rows)
    else:
        summary = build_api_execution_plan(manifest_jsonl=manifest_jsonl)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R383 plain requery control API execution.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--r380_results", default=DEFAULT_R380_RESULTS)
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
