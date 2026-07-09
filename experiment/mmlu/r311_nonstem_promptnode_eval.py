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

from experiment.mmlu.r231_tiny_diagnostic_runner import estimate_request_cost
from experiment.mmlu.r233_tiny_api_diagnostic_executor import load_env_values
from mas_framework.utils.globals import CompletionTokens, Cost, PromptTokens


VALID_LABELS = {"A", "B", "C", "D", "E"}
VALID_ACTIONS = {"KEEP_ARG", "SWITCH"}
DEFAULT_MODEL = "gpt-4o-2024-08-06"
DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_ARG_JSONL = "experiment/mmlu/run_logs/mmlu_r311_nonstem_arg_baseline_results.jsonl"
DEFAULT_SPLIT_JSONL = "experiment/mmlu/run_logs/mmlu_r310_nonstem_transfer_preflight_records.jsonl"
DEFAULT_MANIFEST_JSONL = "experiment/mmlu/run_logs/mmlu_r311_nonstem_promptnode_manifest.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/mmlu/run_logs/mmlu_r311_nonstem_promptnode_results.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r311_nonstem_promptnode_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r311_nonstem_promptnode_report.md"

FORBIDDEN_PROMPT_FIELDS = {
    "task_id",
    "true_answer",
    "gold_answer",
    "is_correct",
    "correctness",
    "evaluation_only",
}


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


def parse_guarded_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        action_match = re.search(r"\b(KEEP_ARG|SWITCH)\b", stripped, flags=re.IGNORECASE)
        label_match = re.search(
            r"(?:final_label|selected_label|answer|option)[\"'\s:=-]+([A-E])",
            stripped,
            flags=re.IGNORECASE,
        )
        confidence_match = re.search(r"confidence[\"'\s:=-]+([A-Za-z]+)", stripped, flags=re.IGNORECASE)
        parsed = {
            "action": action_match.group(1).upper() if action_match else "",
            "final_label": label_match.group(1) if label_match else "",
            "confidence": confidence_match.group(1).lower() if confidence_match else "",
        }
    action = str(parsed.get("action") or "").strip().upper()
    if action not in VALID_ACTIONS:
        action = "KEEP_ARG"
    checks = parsed.get("evidence_checks") or []
    if not isinstance(checks, list):
        checks = [str(checks)]
    return {
        "action": action,
        "final_label": normalize_label(parsed.get("final_label") or parsed.get("selected_label")),
        "confidence": str(parsed.get("confidence") or "").strip().lower(),
        "evidence_checks": [str(item)[:500] for item in checks[:4]],
        "rationale": str(parsed.get("rationale") or "")[:1000],
        "parse_ok": bool(parsed),
    }


def _high_confidence(parsed: Dict[str, Any]) -> bool:
    confidence = str(parsed.get("confidence") or "").strip().lower()
    return confidence in {"high", "very_high", "high_confidence"}


def apply_guarded_response(
    record: Dict[str, Any],
    raw_response: str,
    api_executed: bool,
    api_error: str = "",
) -> Dict[str, Any]:
    output = dict(record)
    eval_only = output.get("evaluation_only", {})
    true_answer = normalize_label(eval_only.get("true_answer"))
    arg_prediction = normalize_label(eval_only.get("arg_prediction"))
    arg_is_correct = arg_prediction == true_answer if true_answer in VALID_LABELS else None

    if output.get("api_required") and api_executed and not api_error:
        parsed = parse_guarded_response(raw_response)
        if parsed["action"] == "SWITCH" and _high_confidence(parsed) and parsed["final_label"] in VALID_LABELS:
            predicted = parsed["final_label"]
            fallback_reason = "guarded_high_confidence_switch"
        else:
            predicted = arg_prediction
            fallback_reason = "guarded_keep_arg"
    elif output.get("api_required"):
        parsed = {
            "action": "KEEP_ARG",
            "final_label": "",
            "confidence": "",
            "evidence_checks": [],
            "rationale": "",
            "parse_ok": False,
        }
        predicted = arg_prediction
        fallback_reason = "api_error_fallback_arg" if api_error else "api_not_executed"
    else:
        parsed = {
            "action": "KEEP_ARG",
            "final_label": arg_prediction,
            "confidence": "deterministic",
            "evidence_checks": [],
            "rationale": "arg_baseline_fixed",
            "parse_ok": True,
        }
        predicted = arg_prediction
        fallback_reason = "deterministic_arg_baseline"

    is_correct = predicted == true_answer if true_answer in VALID_LABELS else None
    output.update(
        {
            "api_executed": bool(api_executed),
            "api_error": api_error,
            "raw_response": raw_response,
            "parsed_guarded_response": parsed,
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
    return output


def _promptnodes(candidate: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"name": "PN_MemoryBridge", "role": "carry compact prior option evidence without hidden labels"},
        {"name": "PN_InstructionAmbiguityVerifier", "role": "detect negation, exception, and scope traps"},
        {"name": "PN_OptionSemanticConsistency", "role": "check whether option text semantically satisfies the stem"},
        {"name": "PN_ContradictionDetector", "role": "reject options contradicted by the visible stem"},
        {"name": "PN_AdversarialVerifier", "role": "try to refute ARG's initial answer before any switch"},
        {"name": "PN_ConsensusConflictResolver", "role": "resolve conflicts by evidence quality, not majority"},
        {"name": "PN_Router", "role": f"default KEEP_ARG; candidate_type={candidate.get('candidate_type', 'none')}"},
    ]


def _promptedges() -> List[Dict[str, str]]:
    return [
        {
            "edge": "item_to_instruction_verifier",
            "permission": "read",
            "text": "Read only the visible item and identify wording traps.",
        },
        {
            "edge": "instruction_verifier_to_adversarial_verifier",
            "permission": "write",
            "text": "Write a compact challenge only if ARG appears to violate the instruction.",
        },
        {
            "edge": "adversarial_verifier_to_router",
            "permission": "forward",
            "text": "Forward SWITCH only with high-confidence evidence for a specific different option.",
        },
        {
            "edge": "router_to_final",
            "permission": "forward",
            "text": "If evidence is weak, ambiguous, or only warns about risk, KEEP_ARG.",
        },
    ]


def _lifecycle_policy() -> Dict[str, str]:
    return {
        "update": "update state only when a concrete option-level conflict is found",
        "compress": "compress warning-only nodes into a risk flag",
        "prune": "prune warning-only nodes before answer override",
        "merge": "merge ARG and verifier when they agree",
        "upgrade": "upgrade only repeatable high-confidence non-STEM checks",
    }


def build_guarded_messages(record: Dict[str, Any]) -> List[Dict[str, str]]:
    visible = record["model_visible_input"]
    lines = [
        "MMLU non-STEM multiple-choice item:",
        str(visible["question"]).strip(),
        "",
        f"Subject: {visible['subject']}",
        f"ARG initial choice: {visible['arg_initial_choice']}",
        "",
        "PromptNode identities:",
    ]
    for node in visible["promptnodes"]:
        lines.append(f"- {node['name']}: {node['role']}")
    lines.extend(["", "PromptEdges:"])
    for edge in visible["promptedges"]:
        lines.append(f"- {edge['edge']}: {edge['permission']}; {edge['text']}")
    lines.extend(["", "Lifecycle policy:"])
    for action, description in visible["lifecycle_policy"].items():
        lines.append(f"- {action}: {description}")
    lines.extend(
        [
            "",
            "Decision contract:",
            "- Default action is KEEP_ARG.",
            "- SWITCH only if the visible item gives high-confidence evidence that ARG's option is wrong and one different option is correct.",
            "- If the PromptNode candidate is only an ambiguity warning with no concrete answer evidence, KEEP_ARG.",
            "- Do not use hidden labels, task ids, or evaluation metadata.",
            "",
            "Return compact JSON with keys: action, final_label, confidence, evidence_checks, rationale.",
            "Allowed action values: KEEP_ARG or SWITCH.",
            "Allowed final_label values: A, B, C, D, E.",
            "Allowed confidence values: low, medium, high.",
        ]
    )
    return [
        {
            "role": "system",
            "content": "You are a conservative PromptNode/PromptEdge router for non-STEM multiple-choice transfer.",
        },
        {"role": "user", "content": "\n".join(lines)},
    ]


def _scan_leakage(row: Dict[str, Any]) -> Dict[str, Any]:
    prompt_text = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", [])).lower()
    violations: List[Dict[str, str]] = []
    for field in sorted(FORBIDDEN_PROMPT_FIELDS):
        if field.lower() in prompt_text:
            violations.append({"reason": "forbidden_field_in_prompt", "field": field})
    task_id = str(row.get("task_id") or "").lower()
    if task_id and task_id in prompt_text:
        violations.append({"reason": "task_id_in_prompt", "field": "task_id"})
    return {"leakage_pass": not violations, "leakage_violations": len(violations), "leakage_details": violations}


def build_manifest_records(
    arg_rows: List[Dict[str, Any]],
    split_rows: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 160,
) -> List[Dict[str, Any]]:
    split_lookup = {str(row.get("task_id") or ""): row for row in split_rows}
    records: List[Dict[str, Any]] = []
    for arg_row in arg_rows:
        task_id = str(arg_row.get("task_id") or "")
        candidate = dict(split_lookup.get(task_id, {}).get("candidate") or {})
        arg_prediction = normalize_label(arg_row.get("predicted_answer"))
        true_answer = normalize_label(arg_row.get("true_answer"))
        base = {
            "run_id": "R311",
            "task_id": task_id,
            "dataset": "mmlu_nonstem",
            "subject": arg_row.get("subject", ""),
            "model": model,
            "evaluation_only": {
                "true_answer": true_answer,
                "arg_prediction": arg_prediction,
            },
            "candidate": candidate,
            "max_completion_tokens": max_completion_tokens,
            "claim_boundary": "R311 non-STEM transfer diagnostic; no hidden labels in model-visible prompt.",
        }
        records.append(
            {
                **base,
                "control_variant": "arg_baseline_fixed",
                "api_required": False,
                "api_executed": False,
                "model_visible_input": {
                    "question": arg_row.get("question", ""),
                    "subject": arg_row.get("subject", ""),
                    "diagnostic_variant": "arg_baseline_fixed",
                },
                "model_visible_messages": [],
                "leakage_pass": True,
                "leakage_violations": 0,
                "leakage_details": [],
                "estimated_cost": 0.0,
                "prompt_tokens_estimate": 0,
                "pricing_model": model,
            }
        )
        proposed = {
            **base,
            "control_variant": "proposed_nonstem_promptnode_promptedge",
            "api_required": True,
            "api_executed": False,
            "model_visible_input": {
                "question": arg_row.get("question", ""),
                "subject": arg_row.get("subject", ""),
                "diagnostic_variant": "proposed_nonstem_promptnode_promptedge",
                "arg_initial_choice": arg_prediction,
                "promptnodes": _promptnodes(candidate),
                "promptedges": _promptedges(),
                "lifecycle_policy": _lifecycle_policy(),
                "candidate_summary": {
                    "candidate_type": candidate.get("candidate_type", "none"),
                    "candidate_label": candidate.get("candidate_label", ""),
                    "confidence": candidate.get("confidence", 0.0),
                    "evidence_count": candidate.get("evidence_count", 0),
                },
            },
        }
        proposed["model_visible_messages"] = build_guarded_messages(proposed)
        leakage = _scan_leakage(proposed)
        cost = estimate_request_cost(proposed["model_visible_messages"], model, max_completion_tokens)
        proposed.update(
            {
                "leakage_pass": leakage["leakage_pass"],
                "leakage_violations": leakage["leakage_violations"],
                "leakage_details": leakage["leakage_details"],
                "prompt_tokens_estimate": int(cost["prompt_tokens"]),
                "estimated_cost": float(cost["estimated_cost"]),
                "pricing_model": cost["pricing_model"],
            }
        )
        records.append(proposed)
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
        "switches": sum(
            1
            for row in evaluated
            if row.get("parsed_guarded_response", {}).get("action") == "SWITCH"
            and row.get("fallback_reason") == "guarded_high_confidence_switch"
        ),
        "api_required": sum(1 for row in rows if row.get("api_required")),
        "api_executed": sum(1 for row in rows if row.get("api_executed")),
        "api_errors": sum(1 for row in rows if row.get("api_error")),
    }


def summarize_records(records: List[Dict[str, Any]], api_cost: float, prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
    by_variant = {
        variant: _variant_summary([row for row in records if row.get("control_variant") == variant])
        for variant in sorted({str(row.get("control_variant")) for row in records})
    }
    arg = by_variant.get("arg_baseline_fixed", {})
    proposed = by_variant.get("proposed_nonstem_promptnode_promptedge", {})
    arg_correct = int(arg.get("correct", 0))
    proposed_correct = int(proposed.get("correct", 0))
    return {
        "run_id": "R311",
        "title": "MMLU non-STEM guarded PromptNode transfer diagnostic",
        "claim_boundary": "Same-model non-STEM transfer diagnostic. It can support no-harm evidence, not SCI-Q2 readiness by itself.",
        "no_api": False,
        "broad_api": False,
        "records": len(records),
        "tasks": len({str(row.get("task_id")) for row in records}),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in records).items())),
        "by_variant": by_variant,
        "arg_main": f"{arg_correct}/{arg.get('evaluated_records', 0)}",
        "proposed_main": f"{proposed_correct}/{proposed.get('evaluated_records', 0)}",
        "delta_vs_arg": proposed_correct - arg_correct,
        "fix_harm_vs_arg": f"{proposed.get('fixes', 0)}/{proposed.get('harms', 0)}",
        "no_harm": int(proposed.get("harms", 0)) == 0,
        "beats_arg": proposed_correct > arg_correct,
        "api_cost": round(float(api_cost), 6),
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "training_authorized_next": False,
        "sci_q2_ready": False,
        "next_required_run": "R312_result_to_claim_and_ablation_plan",
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
        raise RuntimeError("Pass --execute_api to run R311 API evaluation.")
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
    outputs: List[Dict[str, Any]] = []
    for idx, row in enumerate(records, start=1):
        if row.get("api_required"):
            try:
                response = await gpt_chat.achat(
                    model=row.get("model") or DEFAULT_MODEL,
                    msg=row.get("model_visible_messages") or [],
                    max_tokens=int(row.get("max_completion_tokens") or 160),
                    temperature=0.0,
                )
                outputs.append(apply_guarded_response(row, response or "", api_executed=True))
            except Exception as exc:  # pragma: no cover - API/backend failure path.
                outputs.append(
                    apply_guarded_response(
                        row,
                        "",
                        api_executed=False,
                        api_error=f"{type(exc).__name__}: {exc}",
                    )
                )
        else:
            outputs.append(apply_guarded_response(row, "", api_executed=False))
        if idx % 10 == 0:
            print(f"R311 progress: {idx}/{len(records)} records processed", flush=True)

    summary = summarize_records(
        outputs,
        api_cost=Cost.instance().value,
        prompt_tokens=int(PromptTokens.instance().value),
        completion_tokens=int(CompletionTokens.instance().value),
    )
    summary.update(
        {
            "manifest_jsonl": manifest_jsonl,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
            "env_values_logged": False,
        }
    )
    write_jsonl(output_jsonl, outputs)
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R311 MMLU Non-STEM Guarded PromptNode Transfer",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- ARG baseline: `{summary['arg_main']}`",
        f"- Proposed guarded PromptNode: `{summary['proposed_main']}`",
        f"- Delta vs ARG: `{summary['delta_vs_arg']}`",
        f"- Fix/harm vs ARG: `{summary['fix_harm_vs_arg']}`",
        f"- No harm: `{summary['no_harm']}`",
        f"- Cost: `${summary['api_cost']:.6f}`",
        f"- Prompt/completion tokens: `{summary['prompt_tokens']}/{summary['completion_tokens']}`",
        "",
        "| Variant | Records | Correct | Accuracy | Fix/Harm | Switches | API executed/errors |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for variant, item in summary["by_variant"].items():
        rows.append(
            f"| `{variant}` | `{item['records']}` | `{item['correct']}` | `{item['accuracy']}` | `{item['fixes']}/{item['harms']}` | `{item['switches']}` | `{item['api_executed']}/{item['api_errors']}` |"
        )
    rows.extend(["", "## Boundary", "", "Use this as transfer/no-harm evidence only after R312 claim audit and ablations.", ""])
    return "\n".join(rows)


def build_and_write_manifest(
    arg_jsonl: str = DEFAULT_ARG_JSONL,
    split_jsonl: str = DEFAULT_SPLIT_JSONL,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 160,
) -> List[Dict[str, Any]]:
    records = build_manifest_records(
        load_jsonl(arg_jsonl),
        load_jsonl(split_jsonl),
        model=model,
        max_completion_tokens=max_completion_tokens,
    )
    write_jsonl(manifest_jsonl, records)
    return records


def run(
    arg_jsonl: str = DEFAULT_ARG_JSONL,
    split_jsonl: str = DEFAULT_SPLIT_JSONL,
    manifest_jsonl: str = DEFAULT_MANIFEST_JSONL,
    env_file: str = DEFAULT_ENV_FILE,
    output_jsonl: str = DEFAULT_OUTPUT_JSONL,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 160,
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
            "run_id": "R311",
            "title": "MMLU non-STEM guarded PromptNode manifest",
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
    parser = argparse.ArgumentParser(description="Run R311 guarded PromptNode non-STEM transfer diagnostic.")
    parser.add_argument("--arg_jsonl", default=DEFAULT_ARG_JSONL)
    parser.add_argument("--split_jsonl", default=DEFAULT_SPLIT_JSONL)
    parser.add_argument("--manifest_jsonl", default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max_completion_tokens", type=int, default=160)
    parser.add_argument("--execute_api", action="store_true")
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
