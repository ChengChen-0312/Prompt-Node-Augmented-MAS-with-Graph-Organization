from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r231_tiny_diagnostic_runner import DEFAULT_MODEL, estimate_request_cost, load_jsonl, normalize_label
from experiment.mmlu.r252_mmlu_transfer_preflight import FORBIDDEN_PROMPT_FIELDS, build_source_lookup


VARIANTS = ["arg_baseline_fixed", "proposed_v3_edge_gated_pnpe"]


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_v3_messages(row: Dict[str, Any]) -> List[Dict[str, str]]:
    visible = row["model_visible_input"]
    lines = [
        "MMLU multiple-choice item:",
        str(visible.get("question") or "").strip(),
        "",
        "Execute an edge-gated PromptNode graph. ARG is a prior, not a gold label.",
        "",
        "PromptNodes:",
        "- PN_Memory: solve independently first and write a compact evidence ledger.",
        "- PN_InstructionVerifier: verify option binding, wording, and at least two evidence checks.",
        "- PN_EdgeGate: decide whether the PromptEdge should forward, prune, compress, or merge evidence.",
        "- PN_Router: emit the final option after reading EdgeGate state.",
        "",
        "PromptEdges:",
        "- item_to_memory/read: independent candidate only.",
        "- memory_to_verifier/write: candidate plus evidence checks.",
        "- verifier_to_edgegate/write: conflict status, option-binding status, and confidence.",
        "- edgegate_to_router/forward: forward only if evidence supports a label; prune if edge text only anchors to ARG.",
        "",
        f"ARG initial choice, visible only after independent solving: {visible.get('arg_initial_choice')}",
        "",
        "Routing policy:",
        "- SWITCH when the independent candidate differs from ARG and two concrete checks support the same label.",
        "- KEEP_ARG when the independent candidate agrees with ARG or when conflict remains unresolved.",
        "- For expression/equation/all-of-the-above items, explicitly test option binding before deciding.",
        "- Do not keep ARG merely because it is the initial graph answer.",
        "",
        "Return strict JSON with keys: action, final_label, independent_label, confidence, edge_decision, evidence_checks, lifecycle_actions, rationale.",
        "Allowed action values: KEEP_ARG or SWITCH.",
        "Allowed edge_decision values: forward, prune, compress, merge.",
        "Allowed final_label values: A, B, C, D, E.",
    ]
    return [
        {
            "role": "system",
            "content": (
                "You are a leakage-safe PromptNode/PromptEdge router. "
                "Use only the visible question, ARG prior, node identities, edge permissions, and lifecycle policy."
            ),
        },
        {"role": "user", "content": "\n".join(lines)},
    ]


def scan_v3_prompt_leakage(row: Dict[str, Any]) -> Dict[str, Any]:
    text = "\n".join(message.get("content", "") for message in row.get("model_visible_messages", [])).lower()
    violations = []
    for field in sorted(FORBIDDEN_PROMPT_FIELDS | {"evaluation_only", "true_answer", "gold_answer", "task_id"}):
        if field.lower() in text:
            violations.append({"field": field, "reason": "forbidden_prompt_field"})
    task_id = str(row.get("task_id") or "").lower()
    if task_id and task_id in text:
        violations.append({"field": "task_id_value", "reason": "task_id_in_prompt"})
    return {"leakage_violations": len(violations), "leakage_pass": not violations, "violations": violations}


def _build_row(probe_row: Dict[str, Any], source_row: Dict[str, Any], variant: str, model: str, max_completion_tokens: int) -> Dict[str, Any]:
    arg_prediction = normalize_label(probe_row.get("labels", {}).get("predicted_answer") or source_row.get("predicted_answer"))
    row = {
        "run_id": "R278",
        "task_id": probe_row.get("task_id"),
        "dataset": "mmlu",
        "control_variant": variant,
        "selection_role": probe_row.get("selection_role"),
        "api_required": variant == "proposed_v3_edge_gated_pnpe",
        "api_executed": False,
        "model": model,
        "model_visible_input": {
            "question": source_row.get("question", ""),
            "subject": source_row.get("subject", probe_row.get("features", {}).get("subject", "unknown")),
            "arg_initial_choice": arg_prediction,
            "diagnostic_variant": variant,
        },
        "evaluation_only": {
            "true_answer": source_row.get("true_answer"),
            "arg_prediction": arg_prediction,
            "arg_error": probe_row.get("labels", {}).get("arg_error"),
        },
        "deterministic_selected_label": arg_prediction,
        "router_final_schema": {
            "schema_version": "r278_edge_gated_v3_preflight",
            "model_visible_fields": ["question", "subject", "arg_initial_choice", "diagnostic_variant"],
            "forbidden_model_visible_fields": sorted(FORBIDDEN_PROMPT_FIELDS),
            "gold_answer_used": False,
            "promptedge_text_policy": {"edge_text_as_prompt": True, "edge_gate_required": True},
        },
    }
    row["model_visible_messages"] = build_v3_messages(row) if row["api_required"] else []
    leakage = scan_v3_prompt_leakage(row)
    cost = (
        estimate_request_cost(row["model_visible_messages"], model, max_completion_tokens)
        if row["api_required"] and leakage["leakage_pass"]
        else {"prompt_tokens": 0, "max_completion_tokens": max_completion_tokens, "estimated_cost": 0.0, "pricing_model": model}
    )
    row.update(
        {
            "leakage_pass": leakage["leakage_pass"],
            "leakage_violations": leakage["leakage_violations"],
            "leakage_details": leakage["violations"],
            "prompt_tokens_estimate": int(cost["prompt_tokens"]),
            "max_completion_tokens": int(cost["max_completion_tokens"]),
            "estimated_cost": float(cost["estimated_cost"]),
            "pricing_model": cost["pricing_model"],
        }
    )
    return row


def build_v3_records(
    probe_rows: List[Dict[str, Any]],
    source_rows: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 128,
) -> List[Dict[str, Any]]:
    source_lookup = build_source_lookup(source_rows)
    rows: List[Dict[str, Any]] = []
    for probe_row in probe_rows:
        source_row = source_lookup.get(str(probe_row.get("task_id") or ""))
        if not source_row:
            continue
        for variant in VARIANTS:
            rows.append(_build_row(probe_row, source_row, variant, model, max_completion_tokens))
    return rows


def summarize_v3_preflight(records: List[Dict[str, Any]], cost_cap: float) -> Dict[str, Any]:
    task_variants: Dict[str, set[str]] = defaultdict(set)
    for row in records:
        task_variants[str(row.get("task_id"))].add(str(row.get("control_variant")))
    total_cost = round(sum(float(row.get("estimated_cost") or 0.0) for row in records), 6)
    leakage_violations = sum(int(row.get("leakage_violations", 0)) for row in records)
    variant_balance_pass = all(variants == set(VARIANTS) for variants in task_variants.values())
    return {
        "run_id": "R278",
        "title": "MMLU full24 edge-gated v3 preflight",
        "claim_boundary": "Preflight only; no API execution and no transfer claim.",
        "records": len(records),
        "tasks": len(task_variants),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in records).items())),
        "api_required": sum(1 for row in records if row.get("api_required")),
        "leakage_violations": leakage_violations,
        "leakage_pass": leakage_violations == 0,
        "estimated_cost": total_cost,
        "cost_cap": float(cost_cap),
        "estimated_cost_within_cap": total_cost <= float(cost_cap),
        "variant_balance_pass": variant_balance_pass,
        "preflight_pass": leakage_violations == 0 and total_cost <= float(cost_cap) and variant_balance_pass,
        "authorized_api_next": leakage_violations == 0 and total_cost <= float(cost_cap) and variant_balance_pass,
    }


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R278 Edge-Gated V3 Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Records/tasks: `{summary['records']}` / `{summary['tasks']}`",
            f"- Variant counts: `{summary['variant_counts']}`",
            f"- API-required records: `{summary['api_required']}`",
            f"- Leakage violations: `{summary['leakage_violations']}`",
            f"- Estimated cost: `${summary['estimated_cost']:.6f}` / cap `${summary['cost_cap']:.6f}`",
            f"- Preflight pass: `{summary['preflight_pass']}`",
            f"- Authorized API next: `{summary['authorized_api_next']}`",
            "",
        ]
    )


def run(
    probe_jsonl: str = "experiment/mmlu/run_logs/mmlu_r251_mmlu_transfer_probe_full24.jsonl",
    transfer_results_jsonl: str = "experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl",
    output_dir: str = "experiment/mmlu/manifests/r278_edge_gated_v3_full24",
    dryrun_jsonl: str = "experiment/mmlu/run_logs/mmlu_r278_edge_gated_v3_preflight_records.jsonl",
    summary_json: str = "experiment/mmlu/res_logs/mmlu_r278_edge_gated_v3_preflight_summary.json",
    report_md: str = "experiment/mmlu/run_logs/mmlu_r278_edge_gated_v3_preflight.md",
    model: str = DEFAULT_MODEL,
    cost_cap: float = 0.12,
    max_completion_tokens: int = 128,
) -> Dict[str, Any]:
    records = build_v3_records(load_jsonl(probe_jsonl), load_jsonl(transfer_results_jsonl), model, max_completion_tokens)
    os.makedirs(output_dir, exist_ok=True)
    _write_jsonl(os.path.join(output_dir, "mmlu_r278_v3_manifest_all.jsonl"), records)
    _write_jsonl(dryrun_jsonl, records)
    summary = summarize_v3_preflight(records, cost_cap)
    summary.update(
        {
            "no_api": True,
            "broad_api": False,
            "model": model,
            "probe_jsonl": probe_jsonl,
            "transfer_results_jsonl": transfer_results_jsonl,
            "output_dir": output_dir,
            "dryrun_jsonl": dryrun_jsonl,
            "max_completion_tokens": max_completion_tokens,
        }
    )
    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build R278 edge-gated v3 preflight.")
    parser.add_argument("--probe_jsonl", default="experiment/mmlu/run_logs/mmlu_r251_mmlu_transfer_probe_full24.jsonl")
    parser.add_argument("--transfer_results_jsonl", default="experiment/mmlu/run_logs/mmlu_r162_transfer_eval_results.jsonl")
    parser.add_argument("--output_dir", default="experiment/mmlu/manifests/r278_edge_gated_v3_full24")
    parser.add_argument("--dryrun_jsonl", default="experiment/mmlu/run_logs/mmlu_r278_edge_gated_v3_preflight_records.jsonl")
    parser.add_argument("--summary_json", default="experiment/mmlu/res_logs/mmlu_r278_edge_gated_v3_preflight_summary.json")
    parser.add_argument("--report_md", default="experiment/mmlu/run_logs/mmlu_r278_edge_gated_v3_preflight.md")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--cost_cap", type=float, default=0.12)
    parser.add_argument("--max_completion_tokens", type=int, default=128)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
