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

from experiment.mmlu.r222_control_manifest_leakage_scan import scan_control_rows
from experiment.mmlu.r231_tiny_diagnostic_runner import DEFAULT_MODEL, estimate_request_cost, load_jsonl, normalize_label
from experiment.mmlu.r252_mmlu_transfer_preflight import build_source_lookup


V2_VARIANT = "proposed_v2_independent_guarded_pnpe"
ALL_VARIANTS = ["arg_baseline_fixed", V2_VARIANT]
FORBIDDEN_PROMPT_FIELDS = {
    "task_id",
    "true_answer",
    "gold_answer",
    "is_correct",
    "arg_error",
    "correctness",
    "evaluation_only",
}


def _v2_model_visible_input(
    variant: str,
    probe_row: Dict[str, Any],
    source_row: Dict[str, Any],
) -> Dict[str, Any]:
    baseline = normalize_label(
        probe_row.get("labels", {}).get("predicted_answer") or source_row.get("predicted_answer")
    )
    visible = {
        "question": source_row.get("question", ""),
        "subject": source_row.get("subject", probe_row.get("features", {}).get("subject", "unknown")),
        "diagnostic_variant": variant,
    }
    if variant == V2_VARIANT:
        visible.update(
            {
                "arg_initial_choice": baseline,
                "promptnodes": [
                    "PN_Memory: independently solve before ARG is consulted",
                    "PN_InstructionVerifier: check option binding and produce exactly two evidence checks",
                    "PN_Router: keep ARG unless verifier proves high-confidence conflict",
                ],
                "promptedges": [
                    "item_to_memory/read: independent candidate only",
                    "memory_to_verifier/write: candidate plus two evidence checks",
                    "verifier_to_router/forward: SWITCH only on high-confidence verified conflict; otherwise KEEP_ARG",
                ],
                "lifecycle": {
                    "update": "verified conflict",
                    "compress": "remove duplicated evidence",
                    "prune": "drop weak candidate",
                    "merge": "ARG and independent candidate agree",
                    "upgrade": "verified pattern reusable for future selector",
                },
            }
        )
    return visible


def build_v2_messages(row: Dict[str, Any]) -> List[Dict[str, str]]:
    visible = row.get("model_visible_input", {})
    lines = [
        "MMLU multiple-choice item:",
        str(visible.get("question") or "").strip(),
        "",
        "Execute PromptNode/PromptEdge v2 in strict order.",
        "",
        "Phase 1 - PN_Memory:",
        "- Solve independently before consulting ARG's initial choice.",
        "- Produce an independent_candidate label.",
        "",
        "Phase 2 - PN_InstructionVerifier:",
        "- Check option binding, arithmetic/formula constraints, and question wording.",
        "- Provide exactly two evidence checks.",
        "- Mark confidence as high only if both checks support the same label.",
        "",
        "Phase 3 - PN_Router:",
        f"- ARG initial choice is now visible: {visible.get('arg_initial_choice', 'NONE')}",
        "- Default action is KEEP_ARG.",
        "- SWITCH only if independent_candidate differs from ARG, confidence is high, and no unresolved conflict remains.",
        "",
        "PromptEdges:",
    ]
    for edge in visible.get("promptedges", []):
        lines.append(f"- {edge}")
    lines.extend(
        [
            "",
            "Return compact JSON with keys: final_label, action, independent_label, confidence, evidence_checks, rationale.",
            "Allowed action values: KEEP_ARG or SWITCH.",
            "Allowed final_label values: A, B, C, D, E.",
        ]
    )
    return [
        {
            "role": "system",
            "content": (
                "You are a leakage-safe guarded PromptNode/PromptEdge router for STEM multiple-choice tasks. "
                "Use only visible item text and graph contracts."
            ),
        },
        {"role": "user", "content": "\n".join(lines)},
    ]


def scan_v2_prompt_leakage(row: Dict[str, Any]) -> Dict[str, Any]:
    base = scan_control_rows([row])
    prompt_text = "\n".join(
        message.get("content", "") for message in row.get("model_visible_messages", [])
    ).lower()
    violations = list(base.get("violations", []))
    for field in sorted(FORBIDDEN_PROMPT_FIELDS):
        if field.lower() in prompt_text:
            violations.append({"reason": "prompt_forbidden_field", "field": field})
    task_id = str(row.get("task_id") or "").lower()
    if task_id and task_id in prompt_text:
        violations.append({"reason": "prompt_task_id_value", "field": "task_id"})
    return {
        "leakage_violations": len(violations),
        "leakage_pass": len(violations) == 0,
        "violations": violations,
    }


def _build_one(
    probe_row: Dict[str, Any],
    source_row: Dict[str, Any],
    variant: str,
    model: str,
    max_completion_tokens: int,
) -> Dict[str, Any]:
    baseline = normalize_label(
        probe_row.get("labels", {}).get("predicted_answer") or source_row.get("predicted_answer")
    )
    row = {
        "run_id": "R258",
        "task_id": probe_row.get("task_id"),
        "dataset": "mmlu",
        "control_variant": variant,
        "selection_role": probe_row.get("selection_role"),
        "api_required": variant == V2_VARIANT,
        "api_executed": False,
        "model": model,
        "model_visible_input": _v2_model_visible_input(variant, probe_row, source_row),
        "router_final_schema": {
            "schema_version": "r258_promptnode_v2_preflight_v1",
            "model_visible_fields": [
                "question",
                "subject",
                "diagnostic_variant",
                "arg_initial_choice",
                "promptnodes",
                "promptedges",
                "lifecycle",
            ],
            "forbidden_model_visible_fields": sorted(FORBIDDEN_PROMPT_FIELDS),
            "gold_answer_used": False,
            "promptedge_text_policy": {
                "edge_text_as_prompt": True,
                "scope": "compact guarded contracts only",
            },
        },
        "evaluation_only": {
            "true_answer": source_row.get("true_answer"),
            "arg_prediction": baseline,
            "arg_error": probe_row.get("labels", {}).get("arg_error"),
        },
        "deterministic_selected_label": baseline if variant == "arg_baseline_fixed" else "NONE",
    }
    row["model_visible_messages"] = build_v2_messages(row) if row["api_required"] else []
    leakage = scan_v2_prompt_leakage(row)
    cost = (
        estimate_request_cost(row["model_visible_messages"], model, max_completion_tokens)
        if row["api_required"] and leakage["leakage_pass"]
        else {
            "prompt_tokens": 0,
            "max_completion_tokens": max_completion_tokens,
            "estimated_cost": 0.0,
            "pricing_model": model,
        }
    )
    row["leakage_pass"] = leakage["leakage_pass"]
    row["leakage_violations"] = leakage["leakage_violations"]
    row["leakage_details"] = leakage["violations"]
    row["prompt_tokens_estimate"] = int(cost["prompt_tokens"])
    row["max_completion_tokens"] = int(cost["max_completion_tokens"])
    row["estimated_cost"] = float(cost["estimated_cost"])
    row["pricing_model"] = cost["pricing_model"]
    return row


def build_v2_manifest_rows(
    probe_rows: List[Dict[str, Any]],
    source_lookup: Dict[str, Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 96,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for probe_row in probe_rows:
        source_row = source_lookup.get(str(probe_row.get("task_id") or ""), {})
        if not source_row:
            continue
        for variant in ALL_VARIANTS:
            rows.append(_build_one(probe_row, source_row, variant, model, max_completion_tokens))
    return rows


def summarize_v2_preflight(rows: List[Dict[str, Any]], cost_cap: float) -> Dict[str, Any]:
    task_variants: Dict[str, set[str]] = defaultdict(set)
    for row in rows:
        task_variants[str(row.get("task_id"))].add(str(row.get("control_variant")))
    total_cost = round(sum(float(row.get("estimated_cost") or 0.0) for row in rows), 6)
    leakage = sum(int(row.get("leakage_violations", 0)) for row in rows)
    variant_balance_pass = all(variants == set(ALL_VARIANTS) for variants in task_variants.values())
    return {
        "records": len(rows),
        "tasks": len(task_variants),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in rows).items())),
        "api_required": sum(1 for row in rows if row.get("api_required")),
        "deterministic_records": sum(1 for row in rows if not row.get("api_required")),
        "leakage_violations": leakage,
        "leakage_pass": leakage == 0,
        "estimated_cost": total_cost,
        "cost_cap": float(cost_cap),
        "estimated_cost_within_cap": total_cost <= float(cost_cap),
        "variant_balance_pass": variant_balance_pass,
        "preflight_pass": leakage == 0 and total_cost <= float(cost_cap) and variant_balance_pass,
    }


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_v2_preflight(
    probe_jsonl: str,
    transfer_results_jsonl: str,
    output_dir: str,
    dryrun_jsonl: str,
    summary_json: str,
    report_md: str,
    model: str,
    cost_cap: float,
    max_completion_tokens: int,
) -> Dict[str, Any]:
    probe_rows = load_jsonl(probe_jsonl)
    source_lookup = build_source_lookup(load_jsonl(transfer_results_jsonl))
    records = build_v2_manifest_rows(
        probe_rows,
        source_lookup,
        model=model,
        max_completion_tokens=max_completion_tokens,
    )
    os.makedirs(output_dir, exist_ok=True)
    _write_jsonl(os.path.join(output_dir, "mmlu_r258_v2_manifest_all.jsonl"), records)
    for variant in ALL_VARIANTS:
        _write_jsonl(
            os.path.join(output_dir, f"mmlu_r258_{variant}.jsonl"),
            [row for row in records if row.get("control_variant") == variant],
        )
    _write_jsonl(dryrun_jsonl, records)
    summary = summarize_v2_preflight(records, cost_cap=cost_cap)
    summary.update(
        {
            "run_id": "R258",
            "title": "PromptNode/PromptEdge v2 preflight",
            "claim_boundary": "Preflight only; no API execution, no accuracy claim, and no SCI-Q2 readiness claim.",
            "no_api": True,
            "broad_api": False,
            "model": model,
            "probe_jsonl": probe_jsonl,
            "transfer_results_jsonl": transfer_results_jsonl,
            "output_dir": output_dir,
            "dryrun_jsonl": dryrun_jsonl,
            "max_completion_tokens": max_completion_tokens,
            "authorized_api_next": bool(summary["preflight_pass"]),
        }
    )
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
            "# R258 PromptNode/PromptEdge V2 Preflight",
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
            "## Boundary",
            "",
            "This run only materializes v2 manifests and cost/leakage checks. It does not call the model.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build v2 PromptNode/PromptEdge preflight manifests.")
    parser.add_argument("--probe_jsonl", required=True)
    parser.add_argument("--transfer_results_jsonl", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--dryrun_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--cost_cap", type=float, default=0.45)
    parser.add_argument("--max_completion_tokens", type=int, default=96)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_v2_preflight(
        probe_jsonl=args.probe_jsonl,
        transfer_results_jsonl=args.transfer_results_jsonl,
        output_dir=args.output_dir,
        dryrun_jsonl=args.dryrun_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
        model=args.model,
        cost_cap=args.cost_cap,
        max_completion_tokens=args.max_completion_tokens,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
