from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r231_tiny_diagnostic_runner import estimate_request_cost
from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from experiment.mmlu.r311_nonstem_promptnode_eval import parse_guarded_response
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


VALID_LABELS = {"A", "B", "C", "D", "E"}
DEFAULT_MODEL = "gpt-4o-2024-08-06"
DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_ARG_JSONL = "experiment/mmlu/run_logs/mmlu_r311_nonstem_arg_baseline_results.jsonl"
DEFAULT_SPLIT_JSONL = "experiment/mmlu/run_logs/mmlu_r310_nonstem_transfer_preflight_records.jsonl"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r316_promptedge_cost_controls_manifest.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r316_promptedge_cost_controls_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r316_promptedge_cost_controls_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r316_promptedge_cost_controls_report.md"
FORBIDDEN_PROMPT_FIELDS = {"task_id", "true_answer", "gold_answer", "is_correct", "correctness", "evaluation_only"}


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with _repo_path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def normalize_label(value: Any) -> str:
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
        match = re.search(r"(?:selected_label|answer|option)[\"'\s:=-]+([A-E])", stripped, flags=re.IGNORECASE)
        parsed = {"selected_label": match.group(1) if match else ""}
    selected = normalize_label(parsed.get("selected_label") or parsed.get("final_label"))
    return {
        "selected_label": selected,
        "confidence": str(parsed.get("confidence") or "").lower(),
        "rationale": str(parsed.get("rationale") or "")[:1000],
        "parse_ok": bool(parsed) and selected in VALID_LABELS,
    }


def _high_confidence(parsed: Dict[str, Any]) -> bool:
    return str(parsed.get("confidence") or "").strip().lower() in {"high", "very_high", "high_confidence"}


def apply_control_response(
    record: Dict[str, Any],
    raw_response: str,
    api_executed: bool,
    api_error: str = "",
) -> Dict[str, Any]:
    out = dict(record)
    eval_only = out.get("evaluation_only", {})
    true_answer = normalize_label(eval_only.get("true_answer"))
    arg_prediction = normalize_label(eval_only.get("arg_prediction"))
    arg_is_correct = arg_prediction == true_answer if true_answer in VALID_LABELS else None
    variant = str(out.get("control_variant") or "")

    if not out.get("api_required"):
        parsed: Dict[str, Any] = {"selected_label": arg_prediction, "parse_ok": True}
        predicted = arg_prediction
        fallback_reason = "deterministic_arg_baseline"
    elif not api_executed or api_error:
        parsed = {"selected_label": "", "parse_ok": False}
        predicted = arg_prediction
        fallback_reason = "api_error_fallback_arg" if api_error else "api_not_executed"
    elif variant == "plain_requery":
        parsed = parse_plain_response(raw_response)
        predicted = parsed["selected_label"] if parsed["selected_label"] in VALID_LABELS else arg_prediction
        fallback_reason = "plain_requery_answer" if predicted != arg_prediction else "plain_requery_same_or_fallback"
    elif variant == "node_only_no_promptedge_text":
        parsed = parse_guarded_response(raw_response)
        if parsed.get("action") == "SWITCH" and _high_confidence(parsed) and parsed.get("final_label") in VALID_LABELS:
            predicted = parsed["final_label"]
            fallback_reason = "node_only_high_confidence_switch"
        else:
            predicted = arg_prediction
            fallback_reason = "node_only_keep_arg"
    else:
        parsed = {"selected_label": "", "parse_ok": False}
        predicted = arg_prediction
        fallback_reason = "unknown_variant_fallback_arg"

    is_correct = predicted == true_answer if true_answer in VALID_LABELS else None
    out.update(
        {
            "api_executed": bool(api_executed),
            "api_error": api_error,
            "raw_response": raw_response,
            "parsed_control_response": parsed,
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
    return out


def _node_identities(candidate: Dict[str, Any]) -> List[str]:
    return [
        "PN_MemoryBridge: carry compact prior option evidence without hidden labels",
        "PN_InstructionAmbiguityVerifier: detect negation, exception, and scope traps",
        "PN_OptionSemanticConsistency: check whether option text semantically satisfies the stem",
        "PN_ContradictionDetector: reject options contradicted by the visible stem",
        "PN_AdversarialVerifier: try to refute ARG's initial answer before any switch",
        f"PN_Router: default KEEP_ARG; candidate_type={candidate.get('candidate_type', 'none')}",
    ]


def _plain_messages(row: Dict[str, Any]) -> List[Dict[str, str]]:
    question = row["model_visible_input"]["question"]
    return [
        {"role": "system", "content": "You answer non-STEM multiple-choice questions using only the visible item."},
        {
            "role": "user",
            "content": "\n".join(
                [
                    "MMLU non-STEM multiple-choice item:",
                    question.strip(),
                    "",
                    "Solve directly without PromptNodes or PromptEdges.",
                    "Return compact JSON with keys selected_label, confidence, rationale.",
                    "Allowed selected_label values: A, B, C, D, E.",
                ]
            ),
        },
    ]


def _node_only_messages(row: Dict[str, Any]) -> List[Dict[str, str]]:
    visible = row["model_visible_input"]
    lines = [
        "MMLU non-STEM multiple-choice item:",
        str(visible["question"]).strip(),
        "",
        f"Subject: {visible['subject']}",
        f"ARG initial choice: {visible['arg_initial_choice']}",
        "",
        "PromptNode identities:",
    ]
    lines.extend(f"- {node}" for node in visible["promptnodes"])
    lines.extend(
        [
            "",
            "Lifecycle policy:",
            "- update: record concrete conflicts only",
            "- compress: compress warning-only nodes into a risk flag",
            "- prune: prune warning-only nodes before answer override",
            "- merge: merge ARG and verifier when they agree",
            "- upgrade: upgrade only repeatable high-confidence checks",
            "",
            "Decision contract:",
            "- Default action is KEEP_ARG.",
            "- SWITCH only with high-confidence evidence that ARG is wrong and one different option is correct.",
            "- There is no PromptEdge text in this ablation.",
            "",
            "Return compact JSON with keys: action, final_label, confidence, evidence_checks, rationale.",
            "Allowed action values: KEEP_ARG or SWITCH.",
        ]
    )
    return [
        {"role": "system", "content": "You are a conservative node-only router for non-STEM multiple-choice transfer."},
        {"role": "user", "content": "\n".join(lines)},
    ]


def _scan_leakage(row: Dict[str, Any]) -> Dict[str, Any]:
    prompt_text = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", [])).lower()
    violations = []
    for field in sorted(FORBIDDEN_PROMPT_FIELDS):
        if field in prompt_text:
            violations.append({"reason": "forbidden_field_in_prompt", "field": field})
    task_id = str(row.get("task_id") or "").lower()
    if task_id and task_id in prompt_text:
        violations.append({"reason": "task_id_in_prompt", "field": "task_id"})
    return {"leakage_pass": not violations, "leakage_violations": len(violations), "leakage_details": violations}


def build_manifest_records(
    arg_rows: List[Dict[str, Any]],
    split_rows: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 128,
) -> List[Dict[str, Any]]:
    split_lookup = {str(row.get("task_id") or ""): row for row in split_rows}
    records: List[Dict[str, Any]] = []
    for arg_row in arg_rows:
        task_id = str(arg_row.get("task_id") or "")
        candidate = dict(split_lookup.get(task_id, {}).get("candidate") or {})
        arg_prediction = normalize_label(arg_row.get("predicted_answer"))
        true_answer = normalize_label(arg_row.get("true_answer"))
        base = {
            "run_id": "R316",
            "task_id": task_id,
            "dataset": "mmlu_nonstem",
            "subject": arg_row.get("subject", ""),
            "model": model,
            "candidate": candidate,
            "evaluation_only": {"true_answer": true_answer, "arg_prediction": arg_prediction},
            "max_completion_tokens": max_completion_tokens,
            "claim_boundary": "R316 promptedge/cost control; no hidden labels in model-visible prompt.",
        }
        variants = [
            ("arg_baseline_fixed", False),
            ("plain_requery", True),
            ("node_only_no_promptedge_text", True),
        ]
        for variant, api_required in variants:
            row = {
                **base,
                "control_variant": variant,
                "api_required": api_required,
                "api_executed": False,
                "model_visible_input": {
                    "question": arg_row.get("question", ""),
                    "subject": arg_row.get("subject", ""),
                    "arg_initial_choice": arg_prediction,
                    "promptnodes": _node_identities(candidate),
                    "diagnostic_variant": variant,
                    "candidate_summary": {
                        "candidate_type": candidate.get("candidate_type", "none"),
                        "candidate_label": candidate.get("candidate_label", ""),
                    },
                },
                "model_visible_messages": [],
            }
            if variant == "plain_requery":
                row["model_visible_messages"] = _plain_messages(row)
            elif variant == "node_only_no_promptedge_text":
                row["model_visible_messages"] = _node_only_messages(row)
            leakage = _scan_leakage(row)
            cost = (
                estimate_request_cost(row["model_visible_messages"], model, max_completion_tokens)
                if api_required and leakage["leakage_pass"]
                else {"prompt_tokens": 0, "max_completion_tokens": max_completion_tokens, "estimated_cost": 0.0, "pricing_model": model}
            )
            row.update(
                {
                    "leakage_pass": leakage["leakage_pass"],
                    "leakage_violations": leakage["leakage_violations"],
                    "leakage_details": leakage["leakage_details"],
                    "prompt_tokens_estimate": int(cost["prompt_tokens"]),
                    "estimated_cost": float(cost["estimated_cost"]),
                    "pricing_model": cost["pricing_model"],
                }
            )
            records.append(row)
    return records


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
        "switches": sum(1 for row in evaluated if normalize_label(row.get("predicted_answer")) != normalize_label(row.get("arg_prediction"))),
        "api_required": sum(1 for row in rows if row.get("api_required")),
        "api_executed": sum(1 for row in rows if row.get("api_executed")),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
    }


def summarize_records(records: List[Dict[str, Any]], api_cost: float, prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
    by_variant = {
        variant: _variant_summary([row for row in records if row.get("control_variant") == variant])
        for variant in sorted({str(row.get("control_variant")) for row in records})
    }
    arg_correct = int(by_variant.get("arg_baseline_fixed", {}).get("correct", 0))
    for item in by_variant.values():
        item["delta_vs_arg"] = int(item.get("correct", 0)) - arg_correct
        item["fix_harm"] = f"{item.get('fixes', 0)}/{item.get('harms', 0)}"
    return {
        "run_id": "R316",
        "title": "PromptEdge text and cost-matched plain requery controls",
        "claim_boundary": "Same non-STEM40 control run. It tests promptedge text removal and direct requery cost controls; it is not a broad claim.",
        "no_api": False,
        "broad_api": False,
        "records": len(records),
        "tasks": len({str(row.get("task_id")) for row in records}),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in records).items())),
        "by_variant": by_variant,
        "api_cost": round(float(api_cost), 6),
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "training_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R317_update_claim_matrix_after_controls",
    }


async def execute_manifest(
    manifest_jsonl: str,
    env_file: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
    execute_api: bool,
) -> Dict[str, Any]:
    if not execute_api:
        raise RuntimeError("Pass --execute_api to run R316 controls.")
    load_env_values(env_file)
    import mas_framework.llm.gpt_chat as gpt_chat

    gpt_chat.MINE_BASE_URL = os.getenv("BASE_URL", "").strip() or None
    gpt_chat.MINE_API_KEY = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not gpt_chat.MINE_API_KEY:
        raise RuntimeError("Missing API_KEY or OPENAI_API_KEY after loading env file.")

    Cost.instance().reset()
    PromptTokens.instance().reset()
    CompletionTokens.instance().reset()

    records = load_jsonl(manifest_jsonl)
    outputs = []
    for idx, row in enumerate(records, start=1):
        if row.get("api_required"):
            try:
                response = await gpt_chat.achat(
                    model=row.get("model") or DEFAULT_MODEL,
                    msg=row.get("model_visible_messages") or [],
                    max_tokens=int(row.get("max_completion_tokens") or 128),
                    temperature=0.0,
                )
                outputs.append(apply_control_response(row, response or "", api_executed=True))
            except Exception as exc:  # pragma: no cover
                outputs.append(apply_control_response(row, "", api_executed=False, api_error=f"{type(exc).__name__}: {exc}"))
        else:
            outputs.append(apply_control_response(row, "", api_executed=False))
        if idx % 15 == 0:
            print(f"R316 progress: {idx}/{len(records)} records processed", flush=True)

    summary = summarize_records(
        outputs,
        api_cost=Cost.instance().value,
        prompt_tokens=int(PromptTokens.instance().value),
        completion_tokens=int(CompletionTokens.instance().value),
    )
    summary.update({"manifest_jsonl": manifest_jsonl, "output_jsonl": output_jsonl, "summary_json": summary_json, "report_md": report_md})
    write_jsonl(output_jsonl, outputs)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R316 PromptEdge And Cost Controls",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Variant | Correct | Accuracy | Delta vs ARG | Fix/Harm | Switches | API executed/errors |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for variant, item in summary["by_variant"].items():
        rows.append(
            f"| `{variant}` | `{item['correct']}/{item['evaluated_records']}` | `{item['accuracy']}` | `{item['delta_vs_arg']}` | `{item['fix_harm']}` | `{item['switches']}` | `{item['api_executed']}/{item['api_errors']}` |"
        )
    rows.extend(["", f"- Cost: `${summary['api_cost']:.6f}`", f"- Tokens: `{summary['prompt_tokens']}/{summary['completion_tokens']}`", ""])
    return "\n".join(rows)


def build_and_write_manifest(
    arg_jsonl: str = DEFAULT_ARG_JSONL,
    split_jsonl: str = DEFAULT_SPLIT_JSONL,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 128,
) -> List[Dict[str, Any]]:
    rows = build_manifest_records(load_jsonl(arg_jsonl), load_jsonl(split_jsonl), model=model, max_completion_tokens=max_completion_tokens)
    write_jsonl(manifest_jsonl, rows)
    return rows


def run(
    arg_jsonl: str = DEFAULT_ARG_JSONL,
    split_jsonl: str = DEFAULT_SPLIT_JSONL,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 128,
    execute_api: bool = False,
) -> Dict[str, Any]:
    manifest = build_and_write_manifest(
        arg_jsonl=arg_jsonl,
        split_jsonl=split_jsonl,
        manifest_jsonl=manifest_jsonl,
        model=model,
        max_completion_tokens=max_completion_tokens,
    )
    if not execute_api:
        summary = {
            "run_id": "R316",
            "title": "PromptEdge text and cost controls manifest",
            "claim_boundary": "Manifest only; pass --execute_api for accuracy.",
            "records": len(manifest),
            "tasks": len({str(row.get("task_id")) for row in manifest}),
            "api_required": sum(1 for row in manifest if row.get("api_required")),
            "estimated_cost": round(sum(float(row.get("estimated_cost") or 0.0) for row in manifest), 6),
            "leakage_violations": sum(int(row.get("leakage_violations") or 0) for row in manifest),
            "authorized_api_next": all(row.get("leakage_pass") for row in manifest),
            "manifest_jsonl": manifest_jsonl,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return summary
    return asyncio.run(
        execute_manifest(
            manifest_jsonl=manifest_jsonl,
            env_file=env_file,
            output_jsonl=output_jsonl,
            summary_json=summary_json,
            report_md=report_md,
            execute_api=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R316 promptedge and cost controls.")
    parser.add_argument("--arg_jsonl", default=DEFAULT_ARG_JSONL)
    parser.add_argument("--split_jsonl", default=DEFAULT_SPLIT_JSONL)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max_completion_tokens", type=int, default=128)
    parser.add_argument("--execute_api", action="store_true")
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
