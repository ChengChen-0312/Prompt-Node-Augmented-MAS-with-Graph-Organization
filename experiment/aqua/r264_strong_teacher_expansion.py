from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_MODEL = "gpt-4o-2024-08-06"
DEFAULT_TARGET_TASK_IDS = ["task_59", "task_139", "task_228"]
DEFAULT_R065_RESULTS = os.path.join(SCRIPT_DIR, "aqua_tail34_objective_guided_selector_results.jsonl")
DEFAULT_ENV_FILE = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env"
DEFAULT_RECORDS_JSONL = os.path.join(SCRIPT_DIR, "run_logs", "aqua_r264_strong_teacher_preflight_records.jsonl")
DEFAULT_OUTPUT_JSONL = os.path.join(SCRIPT_DIR, "run_logs", "aqua_r264_strong_teacher_api_results.jsonl")
DEFAULT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "res_logs", "aqua_r264_strong_teacher_summary.json")
DEFAULT_REPORT_MD = os.path.join(SCRIPT_DIR, "run_logs", "aqua_r264_strong_teacher_report.md")
VALID_LABELS = {"A", "B", "C", "D", "E"}
DEFAULT_PROMPT_USD_PER_1M = 2.50
DEFAULT_COMPLETION_USD_PER_1M = 10.00


STRONG_TEACHER_VARIANTS: List[Dict[str, Any]] = [
    {
        "variant_id": "pn_option_elimination_verifier",
        "node_identity": "Instruction-Verifier PromptNode",
        "edge_identity": "PE_option_evidence_forward",
        "procedure": [
            "Parse the question and each answer option.",
            "Check every option A-E independently before choosing.",
            "Reject options that fail an explicit arithmetic, logic, or wording constraint.",
            "Prefer the option that satisfies the most constraints; abstain only if the item is irreparably ambiguous.",
        ],
        "max_completion_tokens": 900,
    },
    {
        "variant_id": "pn_executable_consistency_verifier",
        "node_identity": "Tool-Resource PromptNode",
        "edge_identity": "PE_program_ledger_write_forward",
        "procedure": [
            "Translate the problem into exact equations, enumeration, or symbolic checks.",
            "Use a compact code-like ledger when useful, but do not call an external tool.",
            "Verify the final option against the derived constraints.",
            "If no option exactly matches, report that in evidence_checks and select the closest defensible option.",
        ],
        "max_completion_tokens": 1000,
    },
    {
        "variant_id": "pe_adversarial_countercheck",
        "node_identity": "Agent-like Critic PromptNode",
        "edge_identity": "PE_counterexample_prompt",
        "procedure": [
            "Act as a critic of the first plausible answer.",
            "Try to construct a counterexample for each option and for the inferred solution.",
            "Choose only after the counterexample search is complete.",
            "Do not reward consensus; reward consistency with the item text.",
        ],
        "max_completion_tokens": 1000,
    },
    {
        "variant_id": "pn_state_ledger_lifecycle_verifier",
        "node_identity": "Memory PromptNode upgraded to Instruction-Verifier",
        "edge_identity": "PE_read_write_update_then_forward",
        "procedure": [
            "Write a compact state ledger of givens, unknowns, constraints, and option tests.",
            "Update the ledger when a conflict is found.",
            "Prune unsupported options and merge equivalent interpretations.",
            "Forward the selected label only when the ledger supports it.",
        ],
        "max_completion_tokens": 1000,
    },
]


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label.startswith("NONE"):
        return "NONE"
    return label[:1] if label[:1] in VALID_LABELS else "NONE"


def load_env_values(env_file: str) -> None:
    if not env_file:
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key:
                os.environ[key] = value


def _approx_token_count(text: str) -> int:
    return max(1, int(len(text) / 4))


def _price_from_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def _request_cost(prompt_tokens: int, completion_tokens: int) -> float:
    prompt_price = _price_from_env("OPEN_GMAS_PROMPT_USD_PER_1M_TOKENS", DEFAULT_PROMPT_USD_PER_1M)
    completion_price = _price_from_env(
        "OPEN_GMAS_COMPLETION_USD_PER_1M_TOKENS",
        DEFAULT_COMPLETION_USD_PER_1M,
    )
    return (prompt_tokens * prompt_price + completion_tokens * completion_price) / 1_000_000.0


def estimate_request_cost(
    messages: List[Dict[str, str]],
    model: str,
    max_completion_tokens: int,
) -> Dict[str, Any]:
    prompt_text = "\n".join(f"{message.get('role', '')}: {message.get('content', '')}" for message in messages)
    prompt_tokens = _approx_token_count(prompt_text)
    return {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "max_completion_tokens": int(max_completion_tokens),
        "estimated_cost": round(_request_cost(prompt_tokens, int(max_completion_tokens)), 6),
        "tokenizer": "approx_chars_per_4_no_tiktoken",
    }


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def build_target_task_rows(
    r065_rows: List[Dict[str, Any]],
    target_task_ids: List[str] | None = None,
) -> List[Dict[str, Any]]:
    wanted = list(target_task_ids or DEFAULT_TARGET_TASK_IDS)
    lookup = {str(row.get("task_id")): row for row in r065_rows}
    targets: List[Dict[str, Any]] = []
    for task_id in wanted:
        if task_id not in lookup:
            raise KeyError(f"Target task_id not found in R065 results: {task_id}")
        row = lookup[task_id]
        if row.get("is_solved"):
            raise ValueError(f"R264 target is not an R065 error: {task_id}")
        targets.append(row)
    return targets


def _build_model_visible_messages(task_row: Dict[str, Any], variant: Dict[str, Any]) -> List[Dict[str, str]]:
    procedure_lines = [f"- {line}" for line in variant["procedure"]]
    user_lines = [
        "AQuA multiple-choice item:",
        str(task_row.get("question") or "").strip(),
        "",
        "PromptNode/PromptEdge graph expansion under test:",
        f"- InputTask --read--> {variant['node_identity']}",
        f"- {variant['node_identity']} --write--> EvidenceLedger",
        f"- EvidenceLedger --forward via {variant['edge_identity']} --> FinalRouter",
        "",
        "General verification procedure:",
        *procedure_lines,
        "",
        "Output constraints:",
        "- Return only compact JSON.",
        "- JSON keys: selected_label, confidence, abstain, evidence_checks, failure_modes.",
        "- selected_label must be one of A, B, C, D, E, or NONE.",
        "- confidence must be a number between 0 and 1.",
        "- evidence_checks should mention the decisive option tests, not hidden metadata.",
        "",
        "Safety rules:",
        "- Use only the visible item text and the general graph procedure above.",
        "- Do not rely on previous system predictions, hidden labels, dataset artifacts, or memorized examples.",
        "- If the exact solution is absent from the choices, say so and select the closest defensible option only under general test-taking semantics.",
    ]
    return [
        {
            "role": "system",
            "content": (
                "You are a leakage-safe strong-teacher PromptNode verifier for multiple-choice reasoning. "
                "You solve from the item text, not from hidden evaluation data."
            ),
        },
        {"role": "user", "content": "\n".join(user_lines)},
    ]


def scan_prompt_leakage(record: Dict[str, Any]) -> Dict[str, Any]:
    text = "\n".join(message.get("content", "") for message in record.get("model_visible_messages", [])).lower()
    forbidden_terms = [
        "task_id",
        "true_answer",
        "gold_answer",
        "baseline_prediction",
        "predicted_answer",
        "is_solved",
        "baseline_is_solved",
        "r065",
        "gold label",
        "ground truth",
    ]
    violations = []
    for term in forbidden_terms:
        if term in text:
            violations.append({"field": term, "pattern": term})
    task_id = str(record.get("task_id") or "").lower()
    if task_id and task_id in text:
        violations.append({"field": "task_id_value", "pattern": task_id})
    return {
        "leakage_pass": len(violations) == 0,
        "leakage_violations": len(violations),
        "violations": violations,
    }


def build_strong_teacher_records(
    target_rows: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for variant in STRONG_TEACHER_VARIANTS:
        for task_row in target_rows:
            messages = _build_model_visible_messages(task_row, variant)
            max_tokens = int(variant.get("max_completion_tokens") or 900)
            record = {
                "run_id": "R264",
                "task_id": str(task_row.get("task_id")),
                "variant_id": variant["variant_id"],
                "model": model,
                "max_completion_tokens": max_tokens,
                "temperature": 0.0,
                "api_required": True,
                "model_visible_messages": messages,
                "promptnode_graph": {
                    "nodes": [
                        {"id": "InputTask", "type": "task"},
                        {"id": variant["node_identity"], "type": variant["node_identity"]},
                        {"id": "EvidenceLedger", "type": "Memory"},
                        {"id": "FinalRouter", "type": "Router"},
                    ],
                    "edges": [
                        {"source": "InputTask", "target": variant["node_identity"], "permission": "read"},
                        {"source": variant["node_identity"], "target": "EvidenceLedger", "permission": "write"},
                        {"source": "EvidenceLedger", "target": "FinalRouter", "permission": "forward", "prompt_edge": variant["edge_identity"]},
                    ],
                    "lifecycle_actions": ["update", "prune", "merge", "upgrade"],
                },
                "evaluation_only": {
                    "true_answer": normalize_label(task_row.get("true_answer")),
                    "r065_prediction": normalize_label(task_row.get("predicted_answer")),
                    "arg_prediction": normalize_label(task_row.get("baseline_prediction")),
                    "r065_is_solved": bool(task_row.get("is_solved")),
                },
                "gold_answer_used_in_prompt": False,
                "previous_prediction_used_in_prompt": False,
                "target_task_id_used_in_prompt": False,
            }
            leakage = scan_prompt_leakage(record)
            record["leakage_scan"] = leakage
            record["cost_estimate"] = estimate_request_cost(messages, model, max_tokens)
            records.append(record)
    return records


def _strip_code_fence(text: str) -> str:
    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    return stripped


def _coerce_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.0
    return max(0.0, min(1.0, confidence))


def parse_strong_teacher_response(text: str) -> Dict[str, Any]:
    stripped = _strip_code_fence(text)
    parsed: Dict[str, Any] = {}
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            parsed = data
    except json.JSONDecodeError:
        label_match = re.search(
            r"(?:selected_label|answer|option|label)[\"'\s:=-]+([A-E]|NONE)",
            stripped,
            flags=re.IGNORECASE,
        )
        confidence_match = re.search(r"confidence[\"'\s:=-]+([01](?:\.\d+)?)", stripped, flags=re.IGNORECASE)
        abstain_match = re.search(r"abstain[\"'\s:=-]+(true|false)", stripped, flags=re.IGNORECASE)
        parsed = {
            "selected_label": label_match.group(1) if label_match else "NONE",
            "confidence": confidence_match.group(1) if confidence_match else 0.0,
            "abstain": (
                abstain_match.group(1).lower() == "true"
                if abstain_match
                else (label_match is None and re.search(r"\babstain\b", stripped, flags=re.IGNORECASE) is not None)
            ),
        }

    selected_label = normalize_label(parsed.get("selected_label") or parsed.get("answer") or parsed.get("option"))
    abstain = bool(parsed.get("abstain")) or selected_label == "NONE"
    if selected_label not in VALID_LABELS:
        selected_label = "NONE"
        abstain = True
    return {
        "selected_label": selected_label,
        "confidence": _coerce_confidence(parsed.get("confidence")),
        "abstain": abstain,
        "evidence_checks": parsed.get("evidence_checks") if isinstance(parsed.get("evidence_checks"), list) else [],
        "failure_modes": parsed.get("failure_modes") if isinstance(parsed.get("failure_modes"), list) else [],
        "parse_ok": bool(parsed),
    }


def apply_strong_teacher_response(
    record: Dict[str, Any],
    raw_response: str,
    api_executed: bool,
    api_error: str = "",
) -> Dict[str, Any]:
    output = dict(record)
    eval_only = output.get("evaluation_only", {})
    true_answer = normalize_label(eval_only.get("true_answer"))
    r065_prediction = normalize_label(eval_only.get("r065_prediction"))
    if api_executed and not api_error:
        parsed = parse_strong_teacher_response(raw_response)
    else:
        parsed = {
            "selected_label": "NONE",
            "confidence": 0.0,
            "abstain": True,
            "evidence_checks": [],
            "failure_modes": [],
            "parse_ok": False,
        }
    selected = parsed["selected_label"] if not parsed.get("abstain") else "NONE"
    output.update(
        {
            "api_executed": bool(api_executed),
            "api_error": api_error,
            "raw_response": raw_response,
            "parsed_response": parsed,
            "selected_label": selected,
            "true_answer": true_answer,
            "r065_prediction": r065_prediction,
            "matches_gold": selected == true_answer if selected in VALID_LABELS and true_answer in VALID_LABELS else False,
            "agrees_with_r065": selected == r065_prediction if selected in VALID_LABELS else False,
            "fixes_r065_error": selected == true_answer and r065_prediction != true_answer,
        }
    )
    return output


def _label_votes(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    votes = []
    for row in rows:
        parsed = row.get("parsed_response", {})
        label = normalize_label(row.get("selected_label") or parsed.get("selected_label"))
        if label in VALID_LABELS and not parsed.get("abstain") and not row.get("api_error"):
            votes.append(
                {
                    "label": label,
                    "confidence": _coerce_confidence(parsed.get("confidence")),
                    "variant_id": row.get("variant_id"),
                }
            )
    return votes


def _majority_selection(votes: List[Dict[str, Any]], fallback_label: str, min_agreement: int = 2) -> Dict[str, Any]:
    if not votes:
        return {"selected_label": fallback_label, "reason": "fallback_r065_no_votes", "top_count": 0}
    counts = Counter(vote["label"] for vote in votes)
    top_label, top_count = counts.most_common(1)[0]
    tied = sum(1 for count in counts.values() if count == top_count) > 1
    avg_conf = sum(vote["confidence"] for vote in votes if vote["label"] == top_label) / top_count
    if top_count >= min_agreement and not tied:
        return {
            "selected_label": top_label,
            "reason": "teacher_majority",
            "top_count": top_count,
            "avg_confidence": round(avg_conf, 4),
        }
    return {
        "selected_label": fallback_label,
        "reason": "fallback_r065_no_stable_majority",
        "top_count": top_count,
        "avg_confidence": round(avg_conf, 4),
    }


def _variant_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    evaluated = [row for row in records if not row.get("api_error")]
    correct = sum(1 for row in evaluated if row.get("matches_gold"))
    return {
        "records": len(records),
        "evaluated": len(evaluated),
        "correct_on_target_errors": correct,
        "accuracy_on_target_errors": correct / len(evaluated) if evaluated else None,
        "fixes": sum(1 for row in evaluated if row.get("fixes_r065_error")),
        "label_counts": dict(sorted(Counter(row.get("selected_label") for row in evaluated).items())),
    }


def summarize_teacher_expansion(
    records: List[Dict[str, Any]],
    r065_correct: int = 31,
    total_tasks: int = 34,
    api_cost: float = 0.0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> Dict[str, Any]:
    by_task_rows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_task_rows[str(row.get("task_id"))].append(row)

    task_summaries: List[Dict[str, Any]] = []
    oracle_fixed = []
    non_oracle_fixed = []
    disagreement_flags = []

    for task_id, rows in sorted(by_task_rows.items()):
        eval_only = rows[0].get("evaluation_only", {})
        true_answer = normalize_label(rows[0].get("true_answer") or eval_only.get("true_answer"))
        r065_prediction = normalize_label(rows[0].get("r065_prediction") or eval_only.get("r065_prediction"))
        votes = _label_votes(rows)
        oracle_labels = sorted({vote["label"] for vote in votes if vote["label"] == true_answer})
        oracle_fixed_task = bool(oracle_labels) and r065_prediction != true_answer
        majority = _majority_selection(votes, fallback_label=r065_prediction)
        non_oracle_fixed_task = majority["selected_label"] == true_answer and r065_prediction != true_answer
        if oracle_fixed_task:
            oracle_fixed.append(task_id)
        if non_oracle_fixed_task:
            non_oracle_fixed.append(task_id)

        vote_counts = Counter(vote["label"] for vote in votes)
        top_label = vote_counts.most_common(1)[0][0] if vote_counts else "NONE"
        top_count = vote_counts.most_common(1)[0][1] if vote_counts else 0
        avg_top_confidence = (
            sum(vote["confidence"] for vote in votes if vote["label"] == top_label) / top_count
            if top_count
            else 0.0
        )
        dataset_disagreement_possible = (
            top_label in VALID_LABELS
            and true_answer in VALID_LABELS
            and top_label != true_answer
            and top_count == len(votes)
            and len(votes) >= 2
            and avg_top_confidence >= 0.75
        )
        if dataset_disagreement_possible:
            disagreement_flags.append(task_id)
        task_summaries.append(
            {
                "task_id": task_id,
                "true_answer": true_answer,
                "r065_prediction": r065_prediction,
                "vote_counts": dict(sorted(vote_counts.items())),
                "oracle_fixed": oracle_fixed_task,
                "non_oracle_selection": majority,
                "non_oracle_fixed": non_oracle_fixed_task,
                "dataset_disagreement_possible": dataset_disagreement_possible,
            }
        )

    oracle_correct = min(total_tasks, r065_correct + len(oracle_fixed))
    non_oracle_correct = min(total_tasks, r065_correct + len(non_oracle_fixed))
    by_variant = {
        variant: _variant_summary([row for row in records if row.get("variant_id") == variant])
        for variant in sorted({str(row.get("variant_id")) for row in records})
    }
    estimated_cost = round(
        sum(float(row.get("cost_estimate", {}).get("estimated_cost") or 0.0) for row in records),
        6,
    )
    return {
        "run_id": "R264",
        "title": "R065 error-targeted strong teacher expansion",
        "claim_boundary": (
            "Targeted strong-teacher ceiling on the three R065 errors only. "
            "This is not a deployed robust selector, not a held-out accuracy claim, and not distillation evidence by itself."
        ),
        "model": records[0].get("model") if records else DEFAULT_MODEL,
        "target_task_ids": sorted(by_task_rows),
        "records": len(records),
        "api_executed": sum(1 for row in records if row.get("api_executed")),
        "api_errors": sum(1 for row in records if row.get("api_error")),
        "leakage_pass": all(row.get("leakage_scan", {}).get("leakage_pass") for row in records),
        "leakage_violations": sum(int(row.get("leakage_scan", {}).get("leakage_violations") or 0) for row in records),
        "estimated_cost": estimated_cost,
        "api_cost": round(float(api_cost), 6),
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "r065_accuracy": f"{r065_correct}/{total_tasks}",
        "oracle_fixed_task_ids": sorted(oracle_fixed),
        "oracle_teacher_accuracy": f"{oracle_correct}/{total_tasks}",
        "non_oracle_fixed_task_ids": sorted(non_oracle_fixed),
        "non_oracle_teacher_accuracy": f"{non_oracle_correct}/{total_tasks}",
        "dataset_disagreement_flags": sorted(disagreement_flags),
        "task_summaries": task_summaries,
        "by_variant": by_variant,
        "next": "If oracle_teacher_accuracy exceeds R065, distill the general verifier signal; otherwise audit label noise and do not optimize toward these labels.",
    }


def build_preflight_records(
    r065_results: str,
    target_task_ids: List[str],
    model: str,
    records_jsonl: str,
) -> List[Dict[str, Any]]:
    targets = build_target_task_rows(load_jsonl(r065_results), target_task_ids)
    records = build_strong_teacher_records(targets, model=model)
    write_jsonl(records_jsonl, records)
    return records


def _chat_url(base_url: str) -> str:
    base = str(base_url or "").strip().rstrip("/")
    if not base:
        base = "https://api.openai.com/v1"
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


async def _chat_completion(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    max_tokens: int,
    temperature: float,
    retries: int = 3,
) -> Dict[str, Any]:
    import aiohttp

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = _chat_url(base_url)
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            timeout = aiohttp.ClientTimeout(total=180)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    body = await response.text()
                    if response.status >= 400:
                        raise RuntimeError(f"HTTP {response.status}: {body[:500]}")
                    data = json.loads(body)
                    content = data.get("choices", [{}])[0].get("message", {}).get("content") or ""
                    usage = data.get("usage") or {}
                    return {"content": content, "usage": usage}
        except Exception as exc:  # pragma: no cover - backend/network dependent.
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt == retries:
                raise RuntimeError(last_error)
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(last_error)


async def execute_strong_teacher_records(
    records: List[Dict[str, Any]],
    env_file: str,
) -> Dict[str, Any]:
    load_env_values(env_file)
    base_url = os.getenv("BASE_URL", "").strip()
    api_key = (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("Missing API_KEY or OPENAI_API_KEY after loading env file.")

    outputs: List[Dict[str, Any]] = []
    prompt_tokens = 0
    completion_tokens = 0
    for index, record in enumerate(records, start=1):
        try:
            result = await _chat_completion(
                base_url=base_url,
                api_key=api_key,
                model=record.get("model") or DEFAULT_MODEL,
                messages=record.get("model_visible_messages") or [],
                max_tokens=int(record.get("max_completion_tokens") or 900),
                temperature=float(record.get("temperature") or 0.0),
            )
            usage = result.get("usage") or {}
            prompt_tokens += int(usage.get("prompt_tokens") or 0)
            completion_tokens += int(usage.get("completion_tokens") or 0)
            outputs.append(apply_strong_teacher_response(record, result.get("content") or "", api_executed=True))
        except Exception as exc:  # pragma: no cover - exercised only on API/backend failure.
            outputs.append(
                apply_strong_teacher_response(
                    record,
                    "",
                    api_executed=False,
                    api_error=f"{type(exc).__name__}: {exc}",
                )
            )
        print(f"R264 progress: {index}/{len(records)} records processed", flush=True)
    return {
        "outputs": outputs,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "api_cost": round(_request_cost(prompt_tokens, completion_tokens), 6),
    }


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# R264 R065 Error-Targeted Strong Teacher Expansion",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Model: `{summary['model']}`",
        f"- Target tasks: `{', '.join(summary['target_task_ids'])}`",
        f"- Records/API/errors: `{summary['records']}/{summary['api_executed']}/{summary['api_errors']}`",
        f"- Leakage pass/violations: `{summary['leakage_pass']}` / `{summary['leakage_violations']}`",
        f"- Estimated/API cost: `${summary['estimated_cost']:.6f}` / `${summary['api_cost']:.6f}`",
        f"- Tokens prompt/completion: `{summary['prompt_tokens']}/{summary['completion_tokens']}`",
        f"- R065 accuracy: `{summary['r065_accuracy']}`",
        f"- Oracle teacher accuracy: `{summary['oracle_teacher_accuracy']}` via `{', '.join(summary['oracle_fixed_task_ids']) or 'none'}`",
        f"- Non-oracle majority teacher accuracy: `{summary['non_oracle_teacher_accuracy']}` via `{', '.join(summary['non_oracle_fixed_task_ids']) or 'none'}`",
        f"- Dataset disagreement flags: `{', '.join(summary['dataset_disagreement_flags']) or 'none'}`",
        "",
        "## Task Breakdown",
        "",
        "| Task | Gold | R065 | Votes | Oracle fix | Majority selected | Majority fix | Dataset-disagreement flag |",
        "|---|---:|---:|---|---:|---|---:|---:|",
    ]
    for task in summary["task_summaries"]:
        majority = task["non_oracle_selection"]
        lines.append(
            f"| `{task['task_id']}` | `{task['true_answer']}` | `{task['r065_prediction']}` | `{task['vote_counts']}` | `{task['oracle_fixed']}` | `{majority['selected_label']}` ({majority['reason']}) | `{task['non_oracle_fixed']}` | `{task['dataset_disagreement_possible']}` |"
        )
    lines.extend(
        [
            "",
            "## Variant Breakdown",
            "",
            "| Variant | Records | Correct on target errors | Accuracy | Fixes | Label counts |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for variant, row in summary["by_variant"].items():
        lines.append(
            f"| `{variant}` | `{row['records']}` | `{row['correct_on_target_errors']}` | `{row['accuracy_on_target_errors']}` | `{row['fixes']}` | `{row['label_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary["next"],
            "",
        ]
    )
    return "\n".join(lines)


async def run_r264(
    r065_results: str,
    target_task_ids: List[str],
    model: str,
    records_jsonl: str,
    output_jsonl: str,
    summary_json: str,
    report_md: str,
    env_file: str,
    execute_api: bool,
) -> Dict[str, Any]:
    records = build_preflight_records(
        r065_results=r065_results,
        target_task_ids=target_task_ids,
        model=model,
        records_jsonl=records_jsonl,
    )
    if not all(row.get("leakage_scan", {}).get("leakage_pass") for row in records):
        raise RuntimeError("R264 preflight failed leakage scan; refusing API execution.")
    if execute_api:
        executed = await execute_strong_teacher_records(records, env_file=env_file)
        outputs = executed["outputs"]
        api_cost = float(executed["api_cost"])
        prompt_tokens = int(executed["prompt_tokens"])
        completion_tokens = int(executed["completion_tokens"])
    else:
        outputs = [
            apply_strong_teacher_response(row, "", api_executed=False, api_error="dry_run_no_api")
            for row in records
        ]
        api_cost = 0.0
        prompt_tokens = 0
        completion_tokens = 0
    write_jsonl(output_jsonl, outputs)
    summary = summarize_teacher_expansion(
        outputs,
        r065_correct=31,
        total_tasks=34,
        api_cost=api_cost,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    write_json(summary_json, summary)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R264 R065 error-targeted strong-teacher expansion.")
    parser.add_argument("--r065_results", default=DEFAULT_R065_RESULTS)
    parser.add_argument("--target_task_ids", nargs="*", default=DEFAULT_TARGET_TASK_IDS)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--records_jsonl", default=DEFAULT_RECORDS_JSONL)
    parser.add_argument("--output_jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--env_file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--execute_api", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = asyncio.run(
        run_r264(
            r065_results=args.r065_results,
            target_task_ids=args.target_task_ids,
            model=args.model,
            records_jsonl=args.records_jsonl,
            output_jsonl=args.output_jsonl,
            summary_json=args.summary_json,
            report_md=args.report_md,
            env_file=args.env_file,
            execute_api=args.execute_api,
        )
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
