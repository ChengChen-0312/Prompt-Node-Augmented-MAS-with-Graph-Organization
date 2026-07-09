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
from experiment.mmlu.r335_prospective_selector_eval_api_smoke import (
    DEFAULT_ENV_FILE,
    _label,
    _strip_code_fence,
    parse_plain_response,
)
from experiment.mmlu.r349_fresh_tool_promptnode_eval_preflight import _leakage
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r408_nonmath_curriculum_fresh_manifest.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r409_nonmath_curriculum_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r409_nonmath_curriculum_api_execution_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r409_nonmath_curriculum_api_execution_report.md"


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


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        text = str(value or "").strip().lower()
        if text in {"high", "true", "yes"}:
            return 0.9
        if text in {"medium"}:
            return 0.6
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "pass", "passed"}


def parse_curriculum_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        label = re.search(r"(?:candidate_label|answer|option)[\"'\s:=-]+([A-E])", stripped, flags=re.I)
        confidence = re.search(r"confidence[\"'\s:=-]+([0-9.]+|high|medium|low)", stripped, flags=re.I)
        parsed = {
            "candidate_label": label.group(1) if label else "",
            "confidence": confidence.group(1) if confidence else "",
            "rationale": stripped[:800],
        }
    return {
        "candidate_label": _label(parsed.get("candidate_label") or parsed.get("final_label")),
        "confidence": _as_float(parsed.get("confidence")),
        "node_agreement_count": _as_int(parsed.get("node_agreement_count")),
        "node_disagreement_count": _as_int(parsed.get("node_disagreement_count")),
        "contradiction_count": _as_int(parsed.get("contradiction_count")),
        "ambiguity_flag": _as_bool(parsed.get("ambiguity_flag")),
        "definition_anchor_confidence": _as_float(parsed.get("definition_anchor_confidence")),
        "adversarial_challenge_pass": _as_bool(parsed.get("adversarial_challenge_pass")),
        "nearest_distractor": _label(parsed.get("nearest_distractor")),
        "nearest_distractor_margin": _as_float(parsed.get("nearest_distractor_margin")),
        "option_binding_contract_pass": _as_bool(parsed.get("option_binding_contract_pass")),
        "memory_bridge_write_confidence": _as_float(parsed.get("memory_bridge_write_confidence")),
        "promptnode_outputs": parsed.get("promptnode_outputs") if isinstance(parsed.get("promptnode_outputs"), dict) else {},
        "promptedge_contracts": parsed.get("promptedge_contracts") if isinstance(parsed.get("promptedge_contracts"), dict) else {},
        "rationale": str(parsed.get("rationale") or "")[:1000],
        "abstain_reason": str(parsed.get("abstain_reason") or "")[:400],
        "parse_ok": bool(parsed),
    }


def conservative_curriculum_gate(parsed: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    if not _label(parsed.get("candidate_label")):
        reasons.append("missing_candidate_label")
    if _as_float(parsed.get("confidence")) < 0.85:
        reasons.append("low_confidence")
    if _as_int(parsed.get("node_agreement_count")) < 3:
        reasons.append("low_node_agreement")
    if _as_int(parsed.get("node_disagreement_count")) > 1:
        reasons.append("node_disagreement")
    if _as_int(parsed.get("contradiction_count")) > 0:
        reasons.append("contradiction")
    if _as_bool(parsed.get("ambiguity_flag")):
        reasons.append("ambiguity")
    if not _as_bool(parsed.get("adversarial_challenge_pass")):
        reasons.append("adversarial_challenge_failed")
    if _as_float(parsed.get("nearest_distractor_margin")) < 0.2:
        reasons.append("small_distractor_margin")
    if not _as_bool(parsed.get("option_binding_contract_pass")):
        reasons.append("option_binding_contract_failed")
    if _as_float(parsed.get("memory_bridge_write_confidence")) < 0.6:
        reasons.append("weak_memory_bridge")
    return {"forward": not reasons, "reasons": reasons}


def _curriculum_features(row: Dict[str, Any], parsed: Dict[str, Any], gate: Dict[str, Any]) -> Dict[str, Any]:
    subject = str(row.get("subject") or "")
    return {
        "dataset_family": row.get("dataset_family"),
        "subject_family": subject.split("_")[0] if subject else "",
        "promptnode_family": "nonmath_curriculum",
        "candidate_type": "curriculum_multi_node",
        "candidate_has_answer_label": int(bool(_label(parsed.get("candidate_label")))),
        "candidate_confidence": _as_float(parsed.get("confidence")),
        "node_agreement_count": _as_int(parsed.get("node_agreement_count")),
        "node_disagreement_count": _as_int(parsed.get("node_disagreement_count")),
        "contradiction_count": _as_int(parsed.get("contradiction_count")),
        "ambiguity_flag": int(_as_bool(parsed.get("ambiguity_flag"))),
        "definition_anchor_confidence": _as_float(parsed.get("definition_anchor_confidence")),
        "adversarial_challenge_pass": int(_as_bool(parsed.get("adversarial_challenge_pass"))),
        "nearest_distractor_margin": _as_float(parsed.get("nearest_distractor_margin")),
        "option_binding_contract_pass": int(_as_bool(parsed.get("option_binding_contract_pass"))),
        "memory_bridge_write_confidence": _as_float(parsed.get("memory_bridge_write_confidence")),
        "gate_forward": int(bool(gate.get("forward"))),
        "gate_block_reasons": ",".join(gate.get("reasons") or []),
        "model_visible_features_only": 1,
        "role_has_pn_instructionverifier": 1,
        "role_has_pn_optionbindingverifier": 1,
        "role_has_pn_conceptdefinitionanchor": 1,
        "role_has_pn_contradictiondetector": 1,
        "role_has_pn_adversarialverifier": 1,
        "role_has_pn_consensusconflictresolver": 1,
        "role_has_pn_memorybridge": 1,
        "promptedge_text_present": 1,
        "promptedge_has_read": 1,
        "promptedge_has_write": 1,
        "promptedge_has_forward": 1,
        "lifecycle_has_update": 1,
        "lifecycle_has_write": 1,
        "lifecycle_has_compress": 1,
        "lifecycle_has_prune": 1,
        "lifecycle_has_merge": 1,
        "lifecycle_has_upgrade": 1,
    }


async def _call(row: Dict[str, Any]) -> str:
    import mas_framework.llm.gpt_chat as gpt_chat

    return await gpt_chat.achat(
        model=row.get("model") or "gpt-4o-2024-08-06",
        msg=row.get("model_visible_messages") or [],
        max_tokens=int(row.get("max_completion_tokens") or 420),
        temperature=0.0,
    ) or ""


def build_api_execution_plan(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    tasks = sorted({row.get("task_id") for row in rows})
    return {
        "run_id": "R409",
        "title": "Nonmath curriculum API execution",
        "claim_boundary": "R409 executes the R408 fresh curriculum manifest only when --execute_api is passed.",
        "no_api": True,
        "broad_api": False,
        "tasks": len(tasks),
        "api_calls_planned": len(rows),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_executed": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R409_execute_with_api_or_R410_analyze_if_executed",
    }


async def execute_api(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
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
    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    raw_outputs: List[Dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        try:
            raw = await _call(row)
            if row.get("control_variant") == "arg_baseline_direct_api":
                parsed = parse_plain_response(raw)
                predicted = parsed["selected_label"]
            else:
                parsed = parse_curriculum_response(raw)
                predicted = parsed["candidate_label"]
            out.update(
                {
                    "api_executed": True,
                    "api_error": "",
                    "raw_response": raw,
                    "parsed_response": parsed,
                    "predicted_answer": predicted,
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
                }
            )
        raw_outputs.append(out)

    by_task: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for row in raw_outputs:
        by_task.setdefault(str(row.get("task_id")), {})[str(row.get("control_variant"))] = row

    final_rows: List[Dict[str, Any]] = []
    for task_id, variants in by_task.items():
        baseline_row = variants.get("arg_baseline_direct_api", {})
        candidate_row = variants.get("nonmath_curriculum_candidate_api", {})
        true_answer = _label((baseline_row.get("evaluation_only") or candidate_row.get("evaluation_only") or {}).get("true_answer"))
        baseline = _label(baseline_row.get("predicted_answer")) or "A"
        parsed_candidate = candidate_row.get("parsed_response") or {}
        candidate = _label(parsed_candidate.get("candidate_label") or candidate_row.get("predicted_answer"))
        gate = conservative_curriculum_gate(parsed_candidate)
        final = candidate if gate["forward"] and candidate else baseline
        final_rows.append(
            {
                "run_id": "R409",
                "task_id": task_id,
                "dataset_family": baseline_row.get("dataset_family") or candidate_row.get("dataset_family"),
                "subject": baseline_row.get("subject") or candidate_row.get("subject"),
                "true_answer": true_answer,
                "arg_prediction": baseline,
                "candidate_label": candidate,
                "gate_forward": bool(gate["forward"] and candidate),
                "gate_block_reasons": gate["reasons"],
                "final_prediction": final,
                "arg_correct": baseline == true_answer,
                "candidate_correct": candidate == true_answer if candidate else False,
                "final_correct": final == true_answer,
                "fix": baseline != true_answer and final == true_answer,
                "harm": baseline == true_answer and final != true_answer,
                "wrong_forward": bool(gate["forward"] and candidate and candidate != true_answer),
                "baseline_api_error": baseline_row.get("api_error", ""),
                "candidate_api_error": candidate_row.get("api_error", ""),
                "candidate_features": _curriculum_features(candidate_row, parsed_candidate, gate),
                "candidate_parsed_response": parsed_candidate,
            }
        )
    return final_rows, _summarize(final_rows, raw_outputs)


def _summarize(final_rows: List[Dict[str, Any]], raw_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "run_id": "R409",
        "title": "Nonmath curriculum API execution",
        "claim_boundary": "R409 is a fresh API execution of the R407/R408 nonmath curriculum with a pre-registered conservative gate. It requires R410 analysis before any claim.",
        "no_api": False,
        "broad_api": False,
        "policy_model": "R407_preregistered_conservative_curriculum_gate",
        "tasks": len(final_rows),
        "api_executed": sum(1 for row in raw_outputs if row.get("api_executed")),
        "api_errors": sum(1 for row in raw_outputs if row.get("api_error")),
        "arg_correct": sum(1 for row in final_rows if row.get("arg_correct")),
        "hybrid_correct": sum(1 for row in final_rows if row.get("final_correct")),
        "candidate_correct": sum(1 for row in final_rows if row.get("candidate_correct")),
        "candidate_label_count": sum(1 for row in final_rows if row.get("candidate_label")),
        "gate_forward_count": sum(1 for row in final_rows if row.get("gate_forward")),
        "fixes": sum(1 for row in final_rows if row.get("fix")),
        "harms": sum(1 for row in final_rows if row.get("harm")),
        "wrong_forward_count": sum(1 for row in final_rows if row.get("wrong_forward")),
        "api_cost": round(float(Cost.instance().value), 6),
        "prompt_tokens": int(PromptTokens.instance().value),
        "completion_tokens": int(CompletionTokens.instance().value),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R410_nonmath_curriculum_analysis",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R409 Nonmath Curriculum API Execution",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- API executed/errors: `{summary.get('api_executed', 0)}/{summary.get('api_errors', 0)}`",
            f"- ARG correct: `{summary.get('arg_correct', '-')}`",
            f"- Hybrid correct: `{summary.get('hybrid_correct', '-')}`",
            f"- Candidate correct/labels: `{summary.get('candidate_correct', '-')}/{summary.get('candidate_label_count', '-')}`",
            f"- Gate forward/fix/harm/wrong-forward: `{summary.get('gate_forward_count', '-')}/{summary.get('fixes', '-')}/{summary.get('harms', '-')}/{summary.get('wrong_forward_count', '-')}`",
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
    parser = argparse.ArgumentParser(description="Run R409 nonmath curriculum API execution.")
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
