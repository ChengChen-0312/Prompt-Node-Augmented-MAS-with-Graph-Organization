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

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from experiment.mmlu.r335_prospective_selector_eval_api_smoke import DEFAULT_ENV_FILE, _label, parse_plain_response
from experiment.mmlu.r342_answer_bearing_candidate_generator_api_probe import parse_candidate_response
from experiment.mmlu.r360_source_invariant_graph_policy_retraining import DECISION_THRESHOLD, _clean_features
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r362_source_invariant_fresh_eval_manifest.jsonl"
DEFAULT_TRAINING_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r357_learned_graph_policy_training_manifest.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r363_source_invariant_fresh_eval_api_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r363_source_invariant_fresh_eval_api_execution_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r363_source_invariant_fresh_eval_api_execution_report.md"
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


def _train_gate(training_manifest_jsonl: str = DEFAULT_TRAINING_MANIFEST_JSONL) -> Tuple[DictVectorizer, LogisticRegression]:
    rows = [row for row in _load_jsonl(training_manifest_jsonl) if row.get("split") == "train"]
    vectorizer = DictVectorizer(sparse=True)
    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=0, solver="liblinear")
    x = vectorizer.fit_transform([_clean_features(row["features"]) for row in rows])
    y = [int(bool(row.get("target_forward"))) for row in rows]
    model.fit(x, y)
    return vectorizer, model


def _confidence_value(raw: Any) -> float:
    text = str(raw or "").strip().lower()
    if text in {"high", "very_high", "high_confidence"}:
        return 1.0
    if text in {"medium", "moderate"}:
        return 0.65
    if text in {"low"}:
        return 0.25
    try:
        return float(text)
    except ValueError:
        return 0.0


def _family(parsed: Dict[str, Any]) -> str:
    family = str(parsed.get("verifier_family") or parsed.get("promptnode_family") or "").lower()
    candidate_type = str(parsed.get("candidate_type") or "").lower()
    if "definition" in family or "fallacy" in family:
        return "nonmath_definition"
    if "semantic" in family or "entailment" in family or "passage" in family:
        return "nonmath_semantic"
    if "tool" in family or "numeric" in candidate_type or "formula" in candidate_type or "symbolic" in candidate_type:
        return "tool_resource_numeric"
    if parsed.get("candidate_label"):
        return "tool_or_verifier_other"
    return "none"


def _candidate_features(row: Dict[str, Any], parsed: Dict[str, Any]) -> Dict[str, Any]:
    candidate = _label(parsed.get("candidate_label"))
    confidence = _confidence_value(parsed.get("confidence"))
    evidence_count = int(parsed.get("evidence_count") or 0)
    contract_pass = bool(parsed.get("promptedge_contract_pass")) or (bool(candidate) and confidence >= 0.85 and evidence_count >= 1)
    family = _family({**parsed, "candidate_label": candidate})
    return {
        "dataset_family": row.get("dataset_family", ""),
        "subject_family": str(row.get("subject", "")).split("_")[0],
        "promptnode_family": family,
        "candidate_type": str(parsed.get("candidate_type") or family or "none"),
        "candidate_has_answer_label": int(bool(candidate)),
        "candidate_confidence": confidence,
        "candidate_evidence_count": evidence_count,
        "gate_score": 1.0 if contract_pass else -0.5,
        "gate_hard_veto": int(not contract_pass),
        "model_visible_features_only": 1,
        "promptedge_text_present": 1,
        "promptedge_has_read": 1,
        "promptedge_has_write": int(bool(parsed.get("rationale")) or evidence_count > 0),
        "promptedge_has_forward": int(contract_pass),
        "lifecycle_has_update": int(bool(candidate)),
        "lifecycle_has_write": int(bool(parsed.get("rationale")) or evidence_count > 0),
        "lifecycle_has_compress": 1,
        "lifecycle_has_prune": int(not contract_pass),
        "lifecycle_has_merge": 0,
        "lifecycle_has_upgrade": int(contract_pass),
        "role_has_pn_instructionverifier": 0,
        "role_has_pn_optionbindingverifier": 0,
        "role_has_pn_symbolicverifier": int(family.startswith("tool_resource")),
        "role_has_pn_toolresource": int(family.startswith("tool_resource")),
        "role_has_pn_safetygate": 1,
        "role_has_pn_router": 1,
        "role_has_pn_adversarialverifier": 0,
        "role_has_pn_contradictiondetector": int("contradiction" in str(parsed.get("promptnode_family", "")).lower()),
        "role_has_pn_consensusconflictresolver": int(not contract_pass),
        "role_has_pn_memorybridge": 0,
    }


async def _call(row: Dict[str, Any]) -> str:
    import mas_framework.llm.gpt_chat as gpt_chat

    return await gpt_chat.achat(
        model=row.get("model") or "gpt-4o-2024-08-06",
        msg=row.get("model_visible_messages") or [],
        max_tokens=int(row.get("max_completion_tokens") or 160),
        temperature=0.0,
    ) or ""


def build_api_execution_plan(manifest_jsonl: str = DEFAULT_MANIFEST_JSONL) -> Dict[str, Any]:
    rows = _load_jsonl(manifest_jsonl)
    violations = _leakage(rows)
    tasks = sorted({row.get("task_id") for row in rows})
    return {
        "run_id": "R363",
        "title": "Source-invariant fresh eval API execution",
        "claim_boundary": "R363 executes the R362 fresh manifest when --execute_api is passed. The dry plan performs no API calls.",
        "no_api": True,
        "broad_api": False,
        "policy_model": "R360_source_invariant_graph_policy",
        "policy_threshold": DECISION_THRESHOLD,
        "tasks": len(tasks),
        "api_calls_planned": len(rows),
        "leakage_pass": not violations,
        "leakage_violations": violations,
        "api_executed": False,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R363_execute_with_api_or_R364_analyze_if_executed",
    }


async def execute_api(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    training_manifest_jsonl: str = DEFAULT_TRAINING_MANIFEST_JSONL,
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
    vectorizer, model = _train_gate(training_manifest_jsonl)
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
                parsed = parse_candidate_response(raw)
                predicted = parsed["candidate_label"]
            out.update({"api_executed": True, "api_error": "", "raw_response": raw, "parsed_response": parsed, "predicted_answer": predicted})
        except Exception as exc:
            out.update({"api_executed": False, "api_error": f"{type(exc).__name__}: {exc}", "raw_response": "", "parsed_response": {}, "predicted_answer": ""})
        raw_outputs.append(out)
    by_task: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for row in raw_outputs:
        by_task.setdefault(str(row.get("task_id")), {})[str(row.get("control_variant"))] = row
    final_rows: List[Dict[str, Any]] = []
    for task_id, variants in by_task.items():
        baseline_row = variants.get("arg_baseline_direct_api", {})
        candidate_row = variants.get("promptnode_candidate_api", {})
        true_answer = _label((baseline_row.get("evaluation_only") or candidate_row.get("evaluation_only") or {}).get("true_answer"))
        baseline = _label(baseline_row.get("predicted_answer")) or "A"
        parsed_candidate = candidate_row.get("parsed_response") or {}
        candidate = _label(parsed_candidate.get("candidate_label") or candidate_row.get("predicted_answer"))
        features = _candidate_features(candidate_row, parsed_candidate)
        score = float(model.predict_proba(vectorizer.transform([_clean_features(features)]))[:, 1][0])
        gate_forward = bool(candidate and score >= DECISION_THRESHOLD)
        final = candidate if gate_forward else baseline
        final_rows.append(
            {
                "run_id": "R363",
                "task_id": task_id,
                "dataset_family": baseline_row.get("dataset_family") or candidate_row.get("dataset_family"),
                "subject": baseline_row.get("subject") or candidate_row.get("subject"),
                "true_answer": true_answer,
                "arg_prediction": baseline,
                "candidate_label": candidate,
                "gate_forward_probability": round(score, 6),
                "gate_forward": gate_forward,
                "final_prediction": final,
                "arg_correct": baseline == true_answer,
                "final_correct": final == true_answer,
                "fix": baseline != true_answer and final == true_answer,
                "harm": baseline == true_answer and final != true_answer,
                "baseline_api_error": baseline_row.get("api_error", ""),
                "candidate_api_error": candidate_row.get("api_error", ""),
                "candidate_features": features,
                "candidate_parsed_response": parsed_candidate,
            }
        )
    summary = _summarize(final_rows, raw_outputs)
    return final_rows, summary


def _summarize(final_rows: List[Dict[str, Any]], raw_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "run_id": "R363",
        "title": "Source-invariant fresh eval API execution",
        "claim_boundary": "R363 is a fresh API execution using the R360 source-invariant gate. It still requires R364 analysis before any claim.",
        "no_api": False,
        "broad_api": False,
        "policy_model": "R360_source_invariant_graph_policy",
        "policy_threshold": DECISION_THRESHOLD,
        "tasks": len(final_rows),
        "api_executed": sum(1 for row in raw_outputs if row.get("api_executed")),
        "api_errors": sum(1 for row in raw_outputs if row.get("api_error")),
        "arg_correct": sum(1 for row in final_rows if row.get("arg_correct")),
        "hybrid_correct": sum(1 for row in final_rows if row.get("final_correct")),
        "gate_forward_count": sum(1 for row in final_rows if row.get("gate_forward")),
        "fixes": sum(1 for row in final_rows if row.get("fix")),
        "harms": sum(1 for row in final_rows if row.get("harm")),
        "api_cost": round(float(Cost.instance().value), 6),
        "prompt_tokens": int(PromptTokens.instance().value),
        "completion_tokens": int(CompletionTokens.instance().value),
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "next_required_run": "R364_source_invariant_fresh_eval_analysis",
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R363 Source-Invariant Fresh Eval API Execution",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Tasks: `{summary['tasks']}`",
            f"- API executed/errors: `{summary.get('api_executed', 0)}/{summary.get('api_errors', 0)}`",
            f"- ARG correct: `{summary.get('arg_correct', '-')}`",
            f"- Hybrid correct: `{summary.get('hybrid_correct', '-')}`",
            f"- Gate forward/fix/harm: `{summary.get('gate_forward_count', '-')}/{summary.get('fixes', '-')}/{summary.get('harms', '-')}`",
            f"- Next required run: `{summary['next_required_run']}`",
            "",
        ]
    )


def run(
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    training_manifest_jsonl: str = DEFAULT_TRAINING_MANIFEST_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    execute_api_flag: bool = False,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    if execute_api_flag:
        rows, summary = asyncio.run(execute_api(manifest_jsonl=manifest_jsonl, training_manifest_jsonl=training_manifest_jsonl, env_file=env_file))
        _write_jsonl(output_jsonl, rows)
    else:
        summary = build_api_execution_plan(manifest_jsonl=manifest_jsonl)
    summary.update({"output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R363 source-invariant fresh eval API execution.")
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--training_manifest_jsonl", default=DEFAULT_TRAINING_MANIFEST_JSONL)
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
