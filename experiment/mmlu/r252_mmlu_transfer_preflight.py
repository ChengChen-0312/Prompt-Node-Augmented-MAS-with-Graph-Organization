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
from experiment.mmlu.r231_tiny_diagnostic_runner import (
    DEFAULT_MODEL,
    estimate_request_cost,
    load_jsonl,
    normalize_label,
)


API_VARIANTS = {
    "plain_requery",
    "node_only_no_promptedge_text",
    "proposed_promptnode_promptedge",
}
DETERMINISTIC_VARIANTS = {"arg_baseline_fixed", "abstain_keep_arg"}
ALL_VARIANTS = [
    "arg_baseline_fixed",
    "abstain_keep_arg",
    "plain_requery",
    "node_only_no_promptedge_text",
    "proposed_promptnode_promptedge",
]
FORBIDDEN_PROMPT_FIELDS = {
    "task_id",
    "true_answer",
    "gold_answer",
    "is_correct",
    "arg_error",
    "correctness",
    "evaluation_only",
}
MODEL_VISIBLE_FIELDS = [
    "question",
    "subject",
    "arg_initial_choice",
    "promptnode_identities",
    "promptedge_permissions",
    "lifecycle_policy",
    "diagnostic_variant",
]


def build_source_lookup(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        task_id = str(row.get("task_id") or "")
        if not task_id:
            continue
        lookup[task_id] = {
            "task_id": task_id,
            "dataset": row.get("dataset", "mmlu"),
            "subject": row.get("subject", "unknown"),
            "question": str(row.get("question") or ""),
            "predicted_answer": normalize_label(row.get("predicted_answer")),
            "true_answer": normalize_label(row.get("true_answer")),
            "is_correct": bool(row.get("is_correct")),
        }
    return lookup


def _promptnode_identities() -> List[Dict[str, str]]:
    return [
        {
            "name": "PN_Memory",
            "role": "Store compact option evidence and any reusable constraints.",
        },
        {
            "name": "PN_InstructionVerifier",
            "role": "Check whether the reasoning respects the question and option binding.",
        },
        {
            "name": "PN_Router",
            "role": "Select the final option after reading Memory and Verifier state.",
        },
    ]


def _promptedge_permissions(edge_text_enabled: bool) -> List[Dict[str, Any]]:
    edges = [
        {
            "edge": "item_to_memory",
            "permission": "read",
            "text": "Extract option-relevant evidence without using hidden labels.",
        },
        {
            "edge": "memory_to_verifier",
            "permission": "write",
            "text": "Write a compact conflict and option-binding ledger.",
        },
        {
            "edge": "verifier_to_router",
            "permission": "forward",
            "text": "Forward only checked evidence and the selected option rationale.",
        },
    ]
    if edge_text_enabled:
        return edges
    return [{k: v for k, v in edge.items() if k != "text"} for edge in edges]


def _lifecycle_policy() -> Dict[str, str]:
    return {
        "update": "Keep evidence that resolves conflicts.",
        "compress": "Shorten redundant option evidence.",
        "prune": "Drop unsupported option paths.",
        "merge": "Combine compatible evidence from Memory and Verifier.",
        "upgrade": "Promote a repeatedly useful check into router state.",
    }


def _model_visible_input(
    variant: str,
    probe_row: Dict[str, Any],
    source_row: Dict[str, Any],
) -> Dict[str, Any]:
    baseline = normalize_label(
        probe_row.get("labels", {}).get("predicted_answer") or source_row.get("predicted_answer")
    )
    visible: Dict[str, Any] = {
        "question": source_row.get("question", ""),
        "subject": source_row.get("subject", probe_row.get("features", {}).get("subject", "unknown")),
        "diagnostic_variant": variant,
    }
    if variant in {"node_only_no_promptedge_text", "proposed_promptnode_promptedge"}:
        visible["arg_initial_choice"] = baseline
        visible["promptnode_identities"] = _promptnode_identities()
        visible["promptedge_permissions"] = _promptedge_permissions(
            edge_text_enabled=variant == "proposed_promptnode_promptedge"
        )
        visible["lifecycle_policy"] = _lifecycle_policy()
    return visible


def build_model_visible_messages(row: Dict[str, Any]) -> List[Dict[str, str]]:
    visible = row.get("model_visible_input", {})
    variant = row.get("control_variant")
    lines = [
        "MMLU multiple-choice item:",
        str(visible.get("question") or "").strip(),
        "",
        f"Diagnostic variant: {variant}",
    ]
    if variant in {"node_only_no_promptedge_text", "proposed_promptnode_promptedge"}:
        lines.extend(
            [
                f"ARG initial choice: {visible.get('arg_initial_choice', 'NONE')}",
                "",
                "PromptNode identities:",
            ]
        )
        for node in visible.get("promptnode_identities", []):
            lines.append(f"- {node['name']}: {node['role']}")
        lines.extend(["", "PromptEdges:"])
        for edge in visible.get("promptedge_permissions", []):
            text = f", text={edge['text']}" if "text" in edge else ""
            lines.append(f"- {edge['edge']}: {edge['permission']}{text}")
        lines.extend(["", "Lifecycle policy:"])
        for action, description in visible.get("lifecycle_policy", {}).items():
            lines.append(f"- {action}: {description}")
    elif variant == "plain_requery":
        lines.append("Solve directly without PromptNodes or PromptEdges.")

    lines.extend(
        [
            "",
            "Use only the visible question, choices, and graph instructions.",
            "Return compact JSON with keys selected_label and rationale.",
            "Allowed selected_label values: A, B, C, D, E.",
        ]
    )
    return [
        {
            "role": "system",
            "content": (
                "You answer multiple-choice STEM questions under a leakage-safe diagnostic protocol. "
                "Do not assume hidden evaluation labels."
            ),
        },
        {"role": "user", "content": "\n".join(lines)},
    ]


def scan_manifest_prompt_leakage(row: Dict[str, Any]) -> Dict[str, Any]:
    base = scan_control_rows([row])
    messages = row.get("model_visible_messages", [])
    prompt_text = "\n".join(message.get("content", "") for message in messages).lower()
    violations = list(base.get("violations", []))
    for field in sorted(FORBIDDEN_PROMPT_FIELDS):
        patterns = [field, f"{field}:", f'"{field}"', f"'{field}'"]
        if any(pattern.lower() in prompt_text for pattern in patterns):
            violations.append({"reason": "prompt_forbidden_field", "field": field})
    task_id = str(row.get("task_id") or "").lower()
    if task_id and task_id in prompt_text:
        violations.append({"reason": "prompt_task_id_value", "field": "task_id"})
    return {
        "leakage_violations": len(violations),
        "leakage_pass": len(violations) == 0,
        "violations": violations,
    }


def _build_one_variant(
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
        "run_id": "R252",
        "task_id": probe_row.get("task_id"),
        "dataset": "mmlu",
        "control_variant": variant,
        "selection_role": probe_row.get("selection_role"),
        "api_required": variant in API_VARIANTS,
        "api_executed": False,
        "model": model,
        "model_visible_input": _model_visible_input(variant, probe_row, source_row),
        "router_final_schema": {
            "schema_version": "r252_mmlu_transfer_preflight_v1",
            "model_visible_fields": MODEL_VISIBLE_FIELDS,
            "forbidden_model_visible_fields": sorted(FORBIDDEN_PROMPT_FIELDS),
            "gold_answer_used": False,
            "promptedge_text_policy": {
                "edge_text_as_prompt": variant == "proposed_promptnode_promptedge",
                "scope": "MMLU tiny transfer diagnostic",
            },
        },
        "evaluation_only": {
            "true_answer": source_row.get("true_answer"),
            "arg_prediction": baseline,
            "arg_error": probe_row.get("labels", {}).get("arg_error"),
        },
        "deterministic_selected_label": baseline if variant in DETERMINISTIC_VARIANTS else "NONE",
    }
    row["model_visible_messages"] = build_model_visible_messages(row) if row["api_required"] else []
    leakage = scan_manifest_prompt_leakage(row)
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


def build_variant_manifest_rows(
    probe_rows: List[Dict[str, Any]],
    source_lookup: Dict[str, Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    max_completion_tokens: int = 64,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for probe_row in probe_rows:
        task_id = str(probe_row.get("task_id") or "")
        source_row = source_lookup.get(task_id, {})
        if not source_row:
            continue
        for variant in ALL_VARIANTS:
            rows.append(_build_one_variant(probe_row, source_row, variant, model, max_completion_tokens))
    return rows


def summarize_preflight_records(rows: List[Dict[str, Any]], cost_cap: float) -> Dict[str, Any]:
    task_variants: Dict[str, set[str]] = defaultdict(set)
    for row in rows:
        task_variants[str(row.get("task_id"))].add(str(row.get("control_variant")))
    variant_balance_pass = all(variants == set(ALL_VARIANTS) for variants in task_variants.values())
    total_cost = round(sum(float(row.get("estimated_cost") or 0.0) for row in rows), 6)
    leakage_violations = sum(int(row.get("leakage_violations", 0)) for row in rows)
    return {
        "records": len(rows),
        "tasks": len(task_variants),
        "variant_counts": dict(sorted(Counter(str(row.get("control_variant")) for row in rows).items())),
        "api_required": sum(1 for row in rows if row.get("api_required")),
        "deterministic_records": sum(1 for row in rows if not row.get("api_required")),
        "leakage_violations": leakage_violations,
        "leakage_pass": leakage_violations == 0,
        "estimated_cost": total_cost,
        "cost_cap": float(cost_cap),
        "estimated_cost_within_cap": total_cost <= float(cost_cap),
        "variant_balance_pass": variant_balance_pass,
        "preflight_pass": leakage_violations == 0
        and total_cost <= float(cost_cap)
        and variant_balance_pass,
    }


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_preflight(
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
    source_rows = load_jsonl(transfer_results_jsonl)
    source_lookup = build_source_lookup(source_rows)
    records = build_variant_manifest_rows(
        probe_rows,
        source_lookup,
        model=model,
        max_completion_tokens=max_completion_tokens,
    )
    os.makedirs(output_dir, exist_ok=True)
    _write_jsonl(os.path.join(output_dir, "mmlu_r252_transfer_manifest_all.jsonl"), records)
    for variant in ALL_VARIANTS:
        _write_jsonl(
            os.path.join(output_dir, f"mmlu_r252_{variant}.jsonl"),
            [row for row in records if row.get("control_variant") == variant],
        )
    _write_jsonl(dryrun_jsonl, records)
    summary = summarize_preflight_records(records, cost_cap=cost_cap)
    summary.update(
        {
            "run_id": "R252",
            "title": "MMLU transfer diagnostic preflight",
            "claim_boundary": "Preflight only; no API execution, no transfer accuracy claim, and no SCI-Q2 readiness claim.",
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
            "# R252 MMLU Transfer Diagnostic Preflight",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Model: `{summary['model']}`",
            f"- Records/tasks: `{summary['records']}` / `{summary['tasks']}`",
            f"- Variant counts: `{summary['variant_counts']}`",
            f"- API-required records: `{summary['api_required']}`",
            f"- Leakage violations: `{summary['leakage_violations']}`",
            f"- Estimated cost: `${summary['estimated_cost']:.6f}` / cap `${summary['cost_cap']:.6f}`",
            f"- Variant balance pass: `{summary['variant_balance_pass']}`",
            f"- Preflight pass: `{summary['preflight_pass']}`",
            f"- Authorized API next: `{summary['authorized_api_next']}`",
            "",
            "## Boundary",
            "",
            "This run only materializes leakage-safe manifests and cost estimates. It does not call any model or support a transfer-improvement claim.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build MMLU transfer diagnostic preflight manifests.")
    parser.add_argument("--probe_jsonl", required=True)
    parser.add_argument("--transfer_results_jsonl", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--dryrun_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--cost_cap", type=float, default=0.45)
    parser.add_argument("--max_completion_tokens", type=int, default=64)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_preflight(
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
