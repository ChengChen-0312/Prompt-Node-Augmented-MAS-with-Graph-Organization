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


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r341_answer_bearing_candidate_generator_probe_manifest.jsonl"
DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r342_answer_bearing_candidate_generator_api_probe_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r342_answer_bearing_candidate_generator_api_probe_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r342_answer_bearing_candidate_generator_api_probe_report.md"
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


def parse_candidate_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        label = re.search(r"(?:candidate_label|selected_label|answer|option)[\"'\s:=-]+([A-E])", stripped, flags=re.I)
        conf = re.search(r"confidence[\"'\s:=-]+([A-Za-z0-9_.]+)", stripped, flags=re.I)
        parsed = {
            "candidate_label": label.group(1) if label else "",
            "confidence": conf.group(1) if conf else "",
        }
    try:
        evidence_count = int(parsed.get("evidence_count") or 0)
    except (TypeError, ValueError):
        evidence_count = 0
    return {
        "candidate_label": _label(parsed.get("candidate_label") or parsed.get("selected_label")),
        "confidence": str(parsed.get("confidence") or "").lower(),
        "evidence_count": evidence_count,
        "verifier_family": str(parsed.get("verifier_family") or ""),
        "rationale": str(parsed.get("rationale") or "")[:1000],
        "parse_ok": bool(parsed),
    }


def _leakage(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    violations = []
    for row in rows:
        prompt = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", [])).lower()
        for field in FORBIDDEN_PROMPT_FIELDS:
            if field in prompt:
                violations.append({"task_id": row.get("task_id", ""), "field": field})
    return violations


def build_api_probe_plan(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    return {
        "run_id": "R342",
        "title": "Answer-bearing candidate generator API probe",
        "claim_boundary": "R342 is a 4-call mechanism probe on R337 wrong tasks. It is not a paper claim.",
        "no_api": True,
        "broad_api": False,
        "records": len(rows),
        "api_calls_planned": len(rows),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_executed": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R342_execute_with_api_or_R343_analyze_if_executed",
    }


async def _call(row: Dict[str, Any]) -> str:
    import mas_framework.llm.gpt_chat as gpt_chat

    return await gpt_chat.achat(
        model=row.get("model") or "gpt-4o-2024-08-06",
        msg=row.get("model_visible_messages") or [],
        max_tokens=int(row.get("max_completion_tokens") or 220),
        temperature=0.0,
    ) or ""


async def execute_api_probe(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL, env_file: str = DEFAULT_ENV_FILE) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    if violations:
        raise RuntimeError(f"Leakage violations block API probe: {violations}")
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
            parsed = parse_candidate_response(raw)
            candidate = parsed["candidate_label"]
            true_answer = _label((row.get("evaluation_only") or {}).get("true_answer"))
            baseline = _label(row.get("baseline_prediction"))
            out.update(
                {
                    "api_executed": True,
                    "api_error": "",
                    "raw_response": raw,
                    "parsed_candidate_response": parsed,
                    "candidate_label": candidate,
                    "true_answer": true_answer,
                    "baseline_prediction": baseline,
                    "candidate_is_correct": candidate == true_answer if candidate else False,
                    "candidate_repairs_baseline": bool(candidate and candidate == true_answer and baseline != true_answer),
                    "candidate_harms_baseline": bool(candidate and baseline == true_answer and candidate != true_answer),
                }
            )
        except Exception as exc:
            out.update({"api_executed": False, "api_error": f"{type(exc).__name__}: {exc}", "raw_response": ""})
        outputs.append(out)
    return outputs, summarize_outputs(outputs)


def summarize_outputs(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid = [row for row in rows if row.get("api_executed") and not row.get("api_error")]
    labels = [row.get("candidate_label") for row in valid if row.get("candidate_label")]
    return {
        "run_id": "R342",
        "title": "Answer-bearing candidate generator API probe",
        "claim_boundary": "R342 is a 4-call mechanism probe on R337 wrong tasks. It is not a paper claim.",
        "no_api": False,
        "broad_api": False,
        "records": len(rows),
        "api_calls_planned": len(rows),
        "api_executed": sum(1 for row in rows if row.get("api_executed")),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
        "candidate_label_count": len(labels),
        "candidate_correct_count": sum(1 for row in valid if row.get("candidate_is_correct")),
        "candidate_repairs_baseline_count": sum(1 for row in valid if row.get("candidate_repairs_baseline")),
        "candidate_harms_baseline_count": sum(1 for row in valid if row.get("candidate_harms_baseline")),
        "verifier_family_counts": dict(sorted(Counter(row.get("verifier_family") for row in rows).items())),
        "api_cost": round(float(Cost.instance().value), 6),
        "prompt_tokens": int(PromptTokens.instance().value),
        "completion_tokens": int(CompletionTokens.instance().value),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R343_answer_bearing_candidate_probe_analysis",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R342 Answer-Bearing Candidate Generator API Probe",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records: `{summary['records']}`",
            f"- API executed: `{summary['api_executed']}`",
            f"- Candidate labels: `{summary.get('candidate_label_count', '-')}`",
            f"- Candidate repairs: `{summary.get('candidate_repairs_baseline_count', '-')}`",
            f"- Candidate harms: `{summary.get('candidate_harms_baseline_count', '-')}`",
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
    parser = argparse.ArgumentParser(description="Run R342 answer-bearing verifier API probe.")
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
