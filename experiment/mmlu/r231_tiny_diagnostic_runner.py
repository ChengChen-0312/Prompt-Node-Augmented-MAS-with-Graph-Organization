from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r222_control_manifest_leakage_scan import scan_control_rows
from mas_framework.llm.price import OPENAI_MODEL_INFO, _pricing_model_name, cal_token


DEFAULT_MODEL = "gpt-4o-2024-08-06"
DEFAULT_COST_CAP = 0.45
DEFAULT_MAX_COMPLETION_TOKENS = 48
VALID_LABELS = {"A", "B", "C", "D", "E"}
API_ROUTER_VARIANTS = {"proposed_router_final", "node_only_no_promptedge_text"}
DETERMINISTIC_VARIANTS = {
    "abstain_only_router",
    "random_switch_labels_same_rate",
    "always_switch_to_objective",
}
GENERIC_FORBIDDEN_TERMS = {"answer", "analysis"}


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


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label.startswith("NONE"):
        return "NONE"
    return label[:1] if label[:1] in VALID_LABELS else "NONE"


def build_source_lookup(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        task_id = str(row.get("task_id") or "").strip()
        question = str(row.get("question") or "").strip()
        if not task_id or not question:
            continue
        existing = lookup.get(task_id, {})
        if existing.get("question"):
            continue
        lookup[task_id] = {
            "task_id": task_id,
            "question": question,
            "true_answer": normalize_label(row.get("true_answer") or row.get("gold_answer")),
            "baseline_prediction": normalize_label(row.get("baseline_prediction")),
            "predicted_answer": normalize_label(row.get("predicted_answer")),
            "slice_prefix": row.get("slice_prefix"),
        }
    return lookup


def load_source_lookup(paths: List[str]) -> Dict[str, Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in paths:
        rows.extend(load_jsonl(path))
    return build_source_lookup(rows)


def _variant(row: Dict[str, Any]) -> str:
    return str(row.get("control_variant") or "proposed_router_final")


def _promptedge_enabled(row: Dict[str, Any]) -> bool:
    if _variant(row) == "node_only_no_promptedge_text":
        return False
    policy = row.get("router_final_schema", {}).get("promptedge_text_policy", {})
    if "edge_text_as_prompt" in policy:
        return bool(policy.get("edge_text_as_prompt"))
    return True


def _safe_policy_lines(policy_input: Dict[str, Any]) -> List[str]:
    allowed = [
        "baseline_prediction",
        "objective_prediction",
        "objective_prediction_differs_from_baseline",
        "objective_top_score",
        "baseline_direct_majority",
        "baseline_direct_majority_count",
        "baseline_direct_valid_vote_count",
        "baseline_direct_votes_split",
    ]
    lines = []
    for key in allowed:
        if key in policy_input:
            lines.append(f"- {key}: {policy_input.get(key)}")
    return lines


def build_model_visible_messages(
    manifest_row: Dict[str, Any],
    source_row: Dict[str, Any],
) -> List[Dict[str, str]]:
    policy_input = manifest_row.get("model_visible_input", {})
    edge_text_enabled = _promptedge_enabled(manifest_row)
    variant = _variant(manifest_row)
    policy_lines = _safe_policy_lines(policy_input)
    user_lines = [
        "AQuA multiple-choice item:",
        str(source_row.get("question") or "").strip(),
        "",
        "PromptNode graph primitives:",
        "- PN_Memory reads candidate option evidence and writes a compact state ledger.",
        "- PN_InstructionVerifier checks option binding and conflict signals.",
        "- PN_Router forwards either the baseline option, the objective option, or NONE.",
        "",
        "PromptEdges:",
        f"- memory_to_verifier: read/write, edge_text_enabled={str(edge_text_enabled).lower()}",
        f"- verifier_to_router: forward, edge_text_enabled={str(edge_text_enabled).lower()}",
        f"- diagnostic_variant: {variant}",
        "",
        "Visible policy signals:",
        *policy_lines,
        "",
        "Return only compact JSON with keys: action, selected_label, rationale.",
        "Allowed action values: switch_to_objective or abstain.",
        "Allowed selected_label values: A, B, C, D, E, NONE.",
    ]
    return [
        {
            "role": "system",
            "content": (
                "You are a leakage-safe PromptNode/PromptEdge router. "
                "Use only the visible item text, candidate signals, node identities, and edge permissions. "
                "Do not assume hidden evaluation labels."
            ),
        },
        {"role": "user", "content": "\n".join(user_lines)},
    ]


def _field_patterns(field: str) -> List[str]:
    field = field.lower()
    if field in GENERIC_FORBIDDEN_TERMS:
        return [f'"{field}"', f"'{field}'", f"{field}:", f"{field} ="]
    return [field]


def scan_message_leakage(
    messages: List[Dict[str, str]],
    manifest_row: Dict[str, Any],
) -> Dict[str, Any]:
    text = "\n".join(message.get("content", "") for message in messages).lower()
    schema = manifest_row.get("router_final_schema", {})
    forbidden = set(schema.get("forbidden_model_visible_fields", []))
    forbidden.update(
        {
            "task_id",
            "true_answer",
            "gold_answer",
            "is_correct",
            "correctness",
            "audit_label",
            "target_option_label",
        }
    )
    violations = []
    for field in sorted(forbidden):
        for pattern in _field_patterns(str(field)):
            if pattern and pattern.lower() in text:
                violations.append({"field": field, "pattern": pattern})
                break
    task_id = str(manifest_row.get("task_id") or "").strip().lower()
    if task_id and task_id in text:
        violations.append({"field": "task_id_value", "pattern": task_id})
    return {
        "leakage_violations": len(violations),
        "leakage_pass": len(violations) == 0,
        "violations": violations,
    }


def estimate_request_cost(
    messages: List[Dict[str, str]],
    model: str,
    max_completion_tokens: int,
) -> Dict[str, Any]:
    prompt_text = "\n".join(f"{message.get('role', '')}: {message.get('content', '')}" for message in messages)
    prompt_tokens = int(cal_token(model, prompt_text))
    pricing_model = _pricing_model_name(model)
    input_price = 0.0
    output_price = 0.0
    if pricing_model in OPENAI_MODEL_INFO["gpt-4"]:
        input_price = OPENAI_MODEL_INFO["gpt-4"][pricing_model]["input"]
        output_price = OPENAI_MODEL_INFO["gpt-4"][pricing_model]["output"]
    elif pricing_model in OPENAI_MODEL_INFO["gpt-3.5"]:
        input_price = OPENAI_MODEL_INFO["gpt-3.5"][pricing_model]["input"]
        output_price = OPENAI_MODEL_INFO["gpt-3.5"][pricing_model]["output"]
    estimated_cost = (prompt_tokens * input_price + int(max_completion_tokens) * output_price) / 1000.0
    return {
        "prompt_tokens": prompt_tokens,
        "max_completion_tokens": int(max_completion_tokens),
        "estimated_cost": round(float(estimated_cost), 6),
        "pricing_model": pricing_model,
    }


def _deterministic_plan(row: Dict[str, Any]) -> Dict[str, Any]:
    variant = _variant(row)
    policy_input = row.get("model_visible_input", {})
    baseline = normalize_label(policy_input.get("baseline_prediction"))
    objective = normalize_label(policy_input.get("objective_prediction"))
    random_label = normalize_label(row.get("target_option_label"))

    if variant == "abstain_only_router":
        return {"planned_action": "abstain", "planned_selected_label": baseline}
    if variant == "always_switch_to_objective":
        return {"planned_action": "switch_to_objective", "planned_selected_label": objective}
    if variant == "random_switch_labels_same_rate":
        return {"planned_action": "switch_to_objective", "planned_selected_label": random_label}
    return {"planned_action": "model_router", "planned_selected_label": "NONE"}


def build_diagnostic_record(
    manifest_row: Dict[str, Any],
    source_lookup: Dict[str, Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
) -> Dict[str, Any]:
    task_id = str(manifest_row.get("task_id") or "")
    source_row = source_lookup.get(task_id, {})
    variant = _variant(manifest_row)
    api_required = variant in API_ROUTER_VARIANTS
    manifest_leakage = scan_control_rows([manifest_row])
    messages = build_model_visible_messages(manifest_row, source_row) if api_required and source_row else []
    prompt_leakage = scan_message_leakage(messages, manifest_row) if messages else {
        "leakage_violations": 0,
        "leakage_pass": True,
        "violations": [],
    }
    cost_estimate = (
        estimate_request_cost(messages, model, max_completion_tokens)
        if api_required and messages and prompt_leakage["leakage_pass"]
        else {"prompt_tokens": 0, "max_completion_tokens": int(max_completion_tokens), "estimated_cost": 0.0, "pricing_model": _pricing_model_name(model)}
    )
    plan = _deterministic_plan(manifest_row)
    prompt_text = "\n".join(message.get("content", "") for message in messages)
    return {
        "task_id": task_id,
        "control_variant": variant,
        "split_role": manifest_row.get("split_role"),
        "api_required": bool(api_required),
        "api_executed": False,
        "model": model,
        "source_available": bool(source_row),
        "question": source_row.get("question"),
        "true_answer": source_row.get("true_answer"),
        "baseline_prediction": normalize_label(manifest_row.get("model_visible_input", {}).get("baseline_prediction")),
        "objective_prediction": normalize_label(manifest_row.get("model_visible_input", {}).get("objective_prediction")),
        "planned_action": plan["planned_action"],
        "planned_selected_label": plan["planned_selected_label"],
        "router_action_from_manifest": manifest_row.get("router_action"),
        "promptedge_text_enabled": _promptedge_enabled(manifest_row),
        "model_visible_messages": messages,
        "model_visible_prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest() if prompt_text else "",
        "manifest_leakage_violations": int(manifest_leakage.get("leakage_violations", 0)),
        "prompt_leakage_violations": int(prompt_leakage.get("leakage_violations", 0)),
        "leakage_pass": bool(manifest_leakage.get("leakage_pass") and prompt_leakage.get("leakage_pass")),
        "prompt_tokens_estimate": int(cost_estimate["prompt_tokens"]),
        "max_completion_tokens": int(cost_estimate["max_completion_tokens"]),
        "estimated_cost": float(cost_estimate["estimated_cost"]),
        "pricing_model": cost_estimate["pricing_model"],
    }


def summarize_diagnostic_records(records: List[Dict[str, Any]], cost_cap: float) -> Dict[str, Any]:
    total_estimated_cost = round(sum(float(row.get("estimated_cost") or 0.0) for row in records), 6)
    return {
        "records": len(records),
        "task_ids": sorted({str(row.get("task_id")) for row in records if row.get("task_id")}),
        "api_required": sum(1 for row in records if row.get("api_required")),
        "deterministic_records": sum(1 for row in records if not row.get("api_required")),
        "source_missing": sum(1 for row in records if not row.get("source_available")),
        "leakage_violations": sum(int(row.get("manifest_leakage_violations", 0)) + int(row.get("prompt_leakage_violations", 0)) for row in records),
        "estimated_cost": total_estimated_cost,
        "cost_cap": float(cost_cap),
        "estimated_cost_within_cap": total_estimated_cost <= float(cost_cap),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in records).items())),
        "api_variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in records if row.get("api_required")).items())),
    }


def _expand_paths(patterns: List[str]) -> List[str]:
    paths: List[str] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        paths.extend(matches or [pattern])
    return paths


def select_preflight_task_ids(rows: List[Dict[str, Any]], max_task_ids: int) -> List[str]:
    selected: List[str] = []
    seen = set()
    for row in rows:
        if _variant(row) != "proposed_router_final":
            continue
        task_id = str(row.get("task_id") or "")
        if not task_id or task_id in seen:
            continue
        seen.add(task_id)
        selected.append(task_id)
        if len(selected) >= max_task_ids:
            break
    return selected


def run_tiny_diagnostic_preflight(
    manifest_paths: List[str],
    source_paths: List[str],
    output_jsonl: str,
    summary_json: str,
    report_md: str,
    model: str = DEFAULT_MODEL,
    max_task_ids: int = 4,
    cost_cap: float = DEFAULT_COST_CAP,
    max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
) -> Dict[str, Any]:
    manifest_rows: List[Dict[str, Any]] = []
    for path in manifest_paths:
        manifest_rows.extend(load_jsonl(path))
    selected_task_ids = set(select_preflight_task_ids(manifest_rows, max_task_ids=max_task_ids))
    source_lookup = load_source_lookup(source_paths)
    records = [
        build_diagnostic_record(
            row,
            source_lookup=source_lookup,
            model=model,
            max_completion_tokens=max_completion_tokens,
        )
        for row in manifest_rows
        if str(row.get("task_id") or "") in selected_task_ids
    ]
    summary = summarize_diagnostic_records(records, cost_cap=cost_cap)
    summary.update(
        {
            "run_id": "R231",
            "title": "Tiny diagnostic runner preflight",
            "claim_boundary": "Runner preflight only; no API, no accuracy claim, and no SCI-Q2 readiness claim.",
            "no_api": True,
            "model": model,
            "manifest_paths": manifest_paths,
            "source_paths": source_paths,
            "output_jsonl": output_jsonl,
            "max_task_ids": max_task_ids,
            "max_completion_tokens": max_completion_tokens,
        }
    )
    write_jsonl(output_jsonl, records)
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R231 Tiny Diagnostic Runner Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Result",
            "",
            f"- Model: `{summary['model']}`",
            f"- Task ids: `{summary['task_ids']}`",
            f"- Records: `{summary['records']}`",
            f"- API-required records: `{summary['api_required']}`",
            f"- Deterministic records: `{summary['deterministic_records']}`",
            f"- Source missing: `{summary['source_missing']}`",
            f"- Leakage violations: `{summary['leakage_violations']}`",
            f"- Estimated cost: `${summary['estimated_cost']:.6f}` / cap `${summary['cost_cap']:.6f}`",
            f"- Estimated cost within cap: `{summary['estimated_cost_within_cap']}`",
            f"- Variant counts: `{summary['variant_counts']}`",
            "",
            "## Boundary",
            "",
            "This run only builds leakage-safe model-visible prompts and cost estimates. It does not call an LLM or score accuracy.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight tiny router-final diagnostic runner.")
    parser.add_argument("--manifest_paths", nargs="+", required=True)
    parser.add_argument("--source_paths", nargs="+", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max_task_ids", type=int, default=4)
    parser.add_argument("--cost_cap", type=float, default=DEFAULT_COST_CAP)
    parser.add_argument("--max_completion_tokens", type=int, default=DEFAULT_MAX_COMPLETION_TOKENS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_tiny_diagnostic_preflight(
        manifest_paths=_expand_paths(args.manifest_paths),
        source_paths=_expand_paths(args.source_paths),
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
        model=args.model,
        max_task_ids=args.max_task_ids,
        cost_cap=args.cost_cap,
        max_completion_tokens=args.max_completion_tokens,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
