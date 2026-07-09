from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from experiment.mmlu.r335_prospective_selector_eval_api_smoke import DEFAULT_ENV_FILE, _label
from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import _leakage
from experiment.mmlu.r375_history_guarded_fresh_eval_api_execution import _strip_code_fence
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r399_contrastive_verifier_targeted_manifest.jsonl"
DEFAULT_R395_RESULTS = "experiment/mmlu/run_logs/mmlu_r395_larger_mixed_nonmath_fresh_api_results.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r400_contrastive_verifier_targeted_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r400_contrastive_verifier_targeted_api_execution_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r400_contrastive_verifier_targeted_api_execution_report.md"


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


def _bool_value(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    text = str(raw or "").strip().lower()
    return text in {"true", "1", "yes", "y"}


def parse_contrastive_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        label = re.search(r"(?:candidate_label|selected_label|answer|option)[\"'\s:=-]+([A-E])", stripped, flags=re.I)
        distractor = re.search(r"rejected_distractor_label[\"'\s:=-]+([A-E])", stripped, flags=re.I)
        parsed = {
            "candidate_label": label.group(1) if label else "",
            "rejected_distractor_label": distractor.group(1) if distractor else "",
        }
    try:
        evidence_count = int(parsed.get("evidence_count") or 0)
    except (TypeError, ValueError):
        evidence_count = 0
    return {
        "candidate_label": _label(parsed.get("candidate_label") or parsed.get("selected_label")),
        "confidence": str(parsed.get("confidence") or "").lower(),
        "evidence_count": evidence_count,
        "promptnode_family": str(parsed.get("promptnode_family") or ""),
        "candidate_type": str(parsed.get("candidate_type") or ""),
        "rejected_distractor_label": _label(parsed.get("rejected_distractor_label")),
        "definition_anchor": str(parsed.get("definition_anchor") or "")[:300],
        "evidence_specificity": str(parsed.get("evidence_specificity") or "")[:300],
        "promptedge_contract_pass": _bool_value(parsed.get("promptedge_contract_pass")),
        "rationale": str(parsed.get("rationale") or "")[:1200],
        "parse_ok": bool(parsed),
    }


async def _call(row: Dict[str, Any]) -> str:
    import mas_framework.llm.gpt_chat as gpt_chat

    return await gpt_chat.achat(
        model=row.get("model") or "gpt-4o-2024-08-06",
        msg=row.get("model_visible_messages") or [],
        max_tokens=int(row.get("max_completion_tokens") or 260),
        temperature=0.0,
    ) or ""


def build_api_execution_plan(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    return {
        "run_id": "R400",
        "title": "Contrastive verifier targeted API execution",
        "claim_boundary": "R400 executes the R399 targeted diagnostic manifest only when --execute_api is passed.",
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "api_calls_planned": len(rows),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_executed": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R400_execute_with_api_or_R401_analyze_if_executed",
    }


async def execute_api(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    r395_results: str = DEFAULT_R395_RESULTS,
    env_file: str = DEFAULT_ENV_FILE,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    if violations:
        raise RuntimeError(f"Leakage violations block API execution: {violations}")
    r395_by_task = {row.get("task_id"): row for row in _load_jsonl(r395_results)}
    load_env_values(env_file)
    import mas_framework.llm.gpt_chat as gpt_chat

    gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
    gpt_chat.MINE_API_KEY = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not gpt_chat.MINE_API_KEY:
        raise RuntimeError("Missing API_KEY or OPENAI_API_KEY after loading env file.")
    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    outputs = []
    for row in rows:
        out = dict(row)
        reference = r395_by_task.get(row.get("task_id"), {})
        true_answer = _label((row.get("evaluation_only") or {}).get("true_answer"))
        try:
            raw = await _call(row)
            parsed = parse_contrastive_response(raw)
            candidate = _label(parsed.get("candidate_label"))
            out.update(
                {
                    "api_executed": True,
                    "api_error": "",
                    "raw_response": raw,
                    "parsed_response": parsed,
                    "candidate_label": candidate,
                    "true_answer": true_answer,
                    "candidate_is_correct": candidate == true_answer if candidate else False,
                    "candidate_repairs_arg": bool(candidate and candidate == true_answer and not reference.get("arg_correct")),
                    "candidate_would_harm_arg": bool(candidate and candidate != true_answer and reference.get("arg_correct")),
                }
            )
        except Exception as exc:
            out.update(
                {
                    "api_executed": False,
                    "api_error": f"{type(exc).__name__}: {exc}",
                    "raw_response": "",
                    "parsed_response": {},
                    "candidate_label": "",
                    "true_answer": true_answer,
                    "candidate_is_correct": False,
                    "candidate_repairs_arg": False,
                    "candidate_would_harm_arg": False,
                }
            )
        out.update(
            {
                "r395_arg_prediction": reference.get("arg_prediction"),
                "r395_arg_correct": reference.get("arg_correct"),
                "r395_candidate_label": reference.get("candidate_label"),
                "r395_gate_forward": reference.get("gate_forward"),
                "r395_final_prediction": reference.get("final_prediction"),
                "r395_final_correct": reference.get("final_correct"),
                "r395_wrong_forward": reference.get("wrong_forward"),
            }
        )
        outputs.append(out)
    return outputs, _summarize(outputs)


def _summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "run_id": "R400",
        "title": "Contrastive verifier targeted API execution",
        "claim_boundary": "R400 is a targeted diagnostic probe on R397/R395 error tasks. It is not a fresh paper result.",
        "no_api": False,
        "broad_api": False,
        "records": len(rows),
        "api_executed": sum(1 for row in rows if row.get("api_executed")),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
        "candidate_label_count": sum(1 for row in rows if row.get("candidate_label")),
        "candidate_correct_count": sum(1 for row in rows if row.get("candidate_is_correct")),
        "candidate_repairs_arg_count": sum(1 for row in rows if row.get("candidate_repairs_arg")),
        "candidate_would_harm_arg_count": sum(1 for row in rows if row.get("candidate_would_harm_arg")),
        "contract_pass_count": sum(1 for row in rows if (row.get("parsed_response") or {}).get("promptedge_contract_pass")),
        "api_cost": round(float(Cost.instance().value), 6),
        "prompt_tokens": int(PromptTokens.instance().value),
        "completion_tokens": int(CompletionTokens.instance().value),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R401_contrastive_verifier_targeted_analysis_and_goal_audit",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R400 Contrastive Verifier Targeted API Execution",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['records']}`",
            f"- API executed/errors: `{summary.get('api_executed', 0)}/{summary.get('api_errors', 0)}`",
            f"- Candidate correct/repairs/harm-risk: `{summary.get('candidate_correct_count', '-')}/{summary.get('candidate_repairs_arg_count', '-')}/{summary.get('candidate_would_harm_arg_count', '-')}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    r395_results: str = DEFAULT_R395_RESULTS,
    env_file: str = DEFAULT_ENV_FILE,
    execute_api_flag: bool = False,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    if execute_api_flag:
        rows, summary = asyncio.run(execute_api(manifest_jsonl=manifest_jsonl, r395_results=r395_results, env_file=env_file))
        _write_jsonl(output_jsonl, rows)
    else:
        summary = build_api_execution_plan(manifest_jsonl=manifest_jsonl)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R400 targeted contrastive verifier API execution.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--r395_results", default=DEFAULT_R395_RESULTS)
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
