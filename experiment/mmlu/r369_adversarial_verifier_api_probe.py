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

from experiment.mmlu.r335_prospective_selector_eval_api_smoke import DEFAULT_ENV_FILE, _label
from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from experiment.mmlu.r342_answer_bearing_candidate_generator_api_probe import parse_candidate_response
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r368_adversarial_verifier_preflight_manifest.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r369_adversarial_verifier_api_probe_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r369_adversarial_verifier_api_probe_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r369_adversarial_verifier_api_probe_report.md"
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


def _leakage(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    violations = []
    for row in rows:
        prompt = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", [])).lower()
        for field in FORBIDDEN_PROMPT_FIELDS:
            if field in prompt:
                violations.append({"task_id": row.get("task_id", ""), "variant": row.get("control_variant", ""), "field": field})
    return violations


def _strip_code_fence(text: str) -> str:
    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    return stripped


def parse_verifier_response(text: str) -> Dict[str, Any]:
    base = parse_candidate_response(text)
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        block = re.search(r"block_forward[\"'\s:=-]+(true|false)", stripped, flags=re.I)
        parsed = {"block_forward": block.group(1).lower() == "true"} if block else {}
    base.update(
        {
            "block_forward": bool(parsed.get("block_forward")),
            "promptnode_family": str(parsed.get("promptnode_family") or base.get("verifier_family") or ""),
            "candidate_type": str(parsed.get("candidate_type") or ""),
        }
    )
    return base


async def _call(row: Dict[str, Any]) -> str:
    import mas_framework.llm.gpt_chat as gpt_chat

    return await gpt_chat.achat(
        model=row.get("model") or "gpt-4o-2024-08-06",
        msg=row.get("model_visible_messages") or [],
        max_tokens=int(row.get("max_completion_tokens") or 240),
        temperature=0.0,
    ) or ""


def build_api_probe_plan(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    return {
        "run_id": "R369",
        "title": "Adversarial verifier API probe",
        "claim_boundary": "R369 is a targeted 11-call mechanism probe only. It is not a paper claim.",
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "api_calls_planned": len(rows),
        "variant_counts": dict(sorted(Counter(row.get("control_variant") for row in rows).items())),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_executed": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R369_execute_with_api_or_R370_analyze_if_executed",
    }


async def execute_api_probe(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL, env_file: str = DEFAULT_ENV_FILE) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    if violations:
        raise RuntimeError(f"Leakage violations block R369 API probe: {violations}")
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
        try:
            raw = await _call(row)
            parsed = parse_verifier_response(raw)
            candidate = _label(parsed.get("candidate_label"))
            true_answer = _label((row.get("evaluation_only") or {}).get("true_answer"))
            out.update(
                {
                    "api_executed": True,
                    "api_error": "",
                    "raw_response": raw,
                    "parsed_response": parsed,
                    "candidate_label": candidate,
                    "true_answer": true_answer,
                    "candidate_is_correct": candidate == true_answer if candidate else False,
                    "block_forward": bool(parsed.get("block_forward")),
                }
            )
        except Exception as exc:
            out.update({"api_executed": False, "api_error": f"{type(exc).__name__}: {exc}", "raw_response": ""})
        outputs.append(out)
    return outputs, summarize_outputs(outputs)


def summarize_outputs(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid = [row for row in rows if row.get("api_executed") and not row.get("api_error")]
    adversarial = [row for row in valid if row.get("control_variant") == "adversarial_candidate_verifier_api"]
    domain = [row for row in valid if row.get("control_variant") == "domain_specialized_candidate_api"]
    return {
        "run_id": "R369",
        "title": "Adversarial verifier API probe",
        "claim_boundary": "R369 is a targeted mechanism probe only. It is not a paper claim.",
        "no_api": False,
        "broad_api": False,
        "records": len(rows),
        "api_executed": sum(1 for row in rows if row.get("api_executed")),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
        "adversarial_records": len(adversarial),
        "domain_records": len(domain),
        "adversarial_block_count": sum(1 for row in adversarial if row.get("block_forward")),
        "adversarial_correct_candidate_count": sum(1 for row in adversarial if row.get("candidate_is_correct")),
        "domain_candidate_count": sum(1 for row in domain if row.get("candidate_label")),
        "domain_correct_candidate_count": sum(1 for row in domain if row.get("candidate_is_correct")),
        "api_cost": round(float(Cost.instance().value), 6),
        "prompt_tokens": int(PromptTokens.instance().value),
        "completion_tokens": int(CompletionTokens.instance().value),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R370_adversarial_verifier_probe_analysis",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R369 Adversarial Verifier API Probe",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['records']}`",
            f"- API executed/errors: `{summary.get('api_executed', 0)}/{summary.get('api_errors', 0)}`",
            f"- Domain candidates/correct: `{summary.get('domain_candidate_count', '-')}/{summary.get('domain_correct_candidate_count', '-')}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    execute_api: bool = False,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    if execute_api:
        rows, summary = asyncio.run(execute_api_probe(manifest_jsonl=manifest_jsonl, env_file=env_file))
        _write_jsonl(output_jsonl, rows)
    else:
        summary = build_api_probe_plan(manifest_jsonl=manifest_jsonl)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R369 adversarial verifier API probe.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--execute_api", action="store_true")
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
