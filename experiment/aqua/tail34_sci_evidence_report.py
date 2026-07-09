import argparse
import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


VALID_OPTIONS = {"A", "B", "C", "D", "E"}

DIRECT_SUMMARY_FILES = {
    "ARG baseline": "aqua_tail34_arg_baseline_summary.jsonl",
    "PN router": "aqua_tail34_pn_router_contract_summary.jsonl",
    "PN candidate": "aqua_tail34_pn_candidate_select_summary.jsonl",
    "PN conservative": "aqua_tail34_pn_conservative_router_summary.jsonl",
    "PN calibrated": "aqua_tail34_pn_calibrated_utility_summary.jsonl",
}

RESULT_FILES = {
    "ARG baseline": "aqua_tail34_arg_baseline_results.jsonl",
    "PN router": "aqua_tail34_pn_router_contract_results.jsonl",
    "PN candidate": "aqua_tail34_pn_candidate_select_results.jsonl",
    "PN conservative": "aqua_tail34_pn_conservative_router_results.jsonl",
    "PN calibrated": "aqua_tail34_pn_calibrated_utility_results.jsonl",
    "PN result ensemble": "aqua_tail34_pn_result_ensemble_results.jsonl",
    "Objective-guided selector": "aqua_tail34_objective_guided_selector_results.jsonl",
    "Margin-3 objective selector": "aqua_tail34_margin3_objective_guided_selector_results.jsonl",
}

FULL_SYSTEM_PARTS = [
    "ARG baseline",
    "PN router",
    "PN candidate",
    "PN conservative",
    "PN calibrated",
]


def normalize_option(value: Any) -> Optional[str]:
    if isinstance(value, str):
        option = value.strip().upper().rstrip(".")
        if option in VALID_OPTIONS:
            return option
    return None


def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_json_or_jsonl(path: str | Path) -> Dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return {}
    first_line = text.splitlines()[0]
    return json.loads(first_line if path_str(path).endswith(".jsonl") else text)


def path_str(path: str | Path) -> str:
    return str(path)


def load_audit(path: str | Path) -> Dict[str, Dict[str, Any]]:
    return {str(record["task_id"]): record for record in load_jsonl(path)}


def by_task(records: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(record["task_id"]): record for record in records}


def is_solved(prediction: Any, true_answer: Any) -> bool:
    return normalize_option(prediction) == normalize_option(true_answer)


def ratio(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}"


def _has_promptnode_role(roles: Iterable[Any]) -> bool:
    for role in roles:
        text = str(role).lower()
        if text.startswith("pn_") or "promptnode" in text or "prompt node" in text:
            return True
    return False


def has_promptnode_graph_marker(record: Dict[str, Any]) -> bool:
    graph = record.get("generated_graph")
    if isinstance(graph, dict) and _has_promptnode_role(graph.get("roles") or []):
        return True
    for graph in record.get("candidate_graphs") or []:
        if isinstance(graph, dict) and _has_promptnode_role(graph.get("roles") or []):
            return True
    for variant in record.get("ranked_variants") or []:
        if variant.get("has_prompt_node_graph"):
            return True
    return False


def _audit_label(task_id: str, audit_by_task: Dict[str, Dict[str, Any]]) -> str:
    return str(audit_by_task.get(task_id, {}).get("clean_label", "unknown"))


def _prediction(record: Dict[str, Any]) -> Optional[str]:
    return normalize_option(record.get("predicted_answer"))


def summarize_method(
    name: str,
    records: List[Dict[str, Any]],
    baseline_records: List[Dict[str, Any]],
    audit_by_task: Dict[str, Dict[str, Any]],
    cost: float = 0.0,
    prompt_tokens: float = 0.0,
    completion_tokens: float = 0.0,
    execution_scope: str = "single run",
) -> Dict[str, Any]:
    baseline_by_task = by_task(baseline_records)
    total = len(records)
    solved = 0
    clean_total = clean_solved = 0
    noisy_total = noisy_solved = 0
    baseline_solved = 0
    fixes = harms = 0
    clean_fixes = clean_harms = 0
    noisy_fixes = noisy_harms = 0
    switches = 0
    switch_task_ids: List[str] = []
    promptnode_hits = 0

    for record in records:
        task_id = str(record.get("task_id", ""))
        baseline_record = baseline_by_task.get(task_id, {})
        true_answer = record.get("true_answer", baseline_record.get("true_answer"))
        prediction = _prediction(record)
        baseline_prediction = normalize_option(
            record.get("baseline_prediction", baseline_record.get("predicted_answer"))
        )
        method_correct = is_solved(prediction, true_answer)
        baseline_correct = is_solved(baseline_prediction, true_answer)
        label = _audit_label(task_id, audit_by_task)

        solved += int(method_correct)
        baseline_solved += int(baseline_correct)
        if label == "clean":
            clean_total += 1
            clean_solved += int(method_correct)
        else:
            noisy_total += 1
            noisy_solved += int(method_correct)

        if not baseline_correct and method_correct:
            fixes += 1
            if label == "clean":
                clean_fixes += 1
            else:
                noisy_fixes += 1
        if baseline_correct and not method_correct:
            harms += 1
            if label == "clean":
                clean_harms += 1
            else:
                noisy_harms += 1

        if prediction != baseline_prediction:
            switches += 1
            switch_task_ids.append(task_id)
        promptnode_hits += int(has_promptnode_graph_marker(record))

    cost_per_task = cost / total if total else 0.0
    cost_per_correct = cost / solved if solved else 0.0
    tokens = float(prompt_tokens or 0.0) + float(completion_tokens or 0.0)

    return {
        "variant": name,
        "total": total,
        "solved": solved,
        "overall": ratio(solved, total),
        "accuracy": solved / total if total else 0.0,
        "clean_total": clean_total,
        "clean_solved": clean_solved,
        "clean": ratio(clean_solved, clean_total),
        "noisy_or_ambiguous_total": noisy_total,
        "noisy_or_ambiguous_solved": noisy_solved,
        "noisy_or_ambiguous": ratio(noisy_solved, noisy_total),
        "baseline_solved": baseline_solved,
        "delta_vs_baseline": solved - baseline_solved,
        "fixes": fixes,
        "harms": harms,
        "fix_harm": f"{fixes}/{harms}",
        "clean_fixes": clean_fixes,
        "clean_harms": clean_harms,
        "clean_fix_harm": f"{clean_fixes}/{clean_harms}",
        "noisy_fixes": noisy_fixes,
        "noisy_harms": noisy_harms,
        "noisy_fix_harm": f"{noisy_fixes}/{noisy_harms}",
        "switches": switches,
        "switch_task_ids": switch_task_ids,
        "promptnode_graph_hit_count": promptnode_hits,
        "promptnode_graph_hits": ratio(promptnode_hits, total),
        "cost": round(float(cost or 0.0), 6),
        "prompt_tokens": float(prompt_tokens or 0.0),
        "completion_tokens": float(completion_tokens or 0.0),
        "total_tokens": tokens,
        "cost_per_task": cost_per_task,
        "cost_per_correct": cost_per_correct,
        "tokens_per_task": tokens / total if total else 0.0,
        "execution_scope": execution_scope,
    }


def build_full_system_cost(summaries: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    cost = sum(float(summaries[name].get("cost", 0.0)) for name in FULL_SYSTEM_PARTS)
    prompt_tokens = sum(float(summaries[name].get("prompt_tokens", 0.0)) for name in FULL_SYSTEM_PARTS)
    completion_tokens = sum(
        float(summaries[name].get("completion_tokens", 0.0)) for name in FULL_SYSTEM_PARTS
    )
    return {
        "cost": round(cost, 6),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "execution_scope": "baseline + router + candidate + conservative + calibrated",
    }


def _load_direct_cost_summaries(base_dir: Path) -> Dict[str, Dict[str, Any]]:
    res_dir = base_dir / "res_logs"
    summaries: Dict[str, Dict[str, Any]] = {}
    for name, filename in DIRECT_SUMMARY_FILES.items():
        raw = load_json_or_jsonl(res_dir / filename)
        summaries[name] = {
            "cost": float(raw.get("cost", 0.0)),
            "prompt_tokens": float(raw.get("prompt_tokens", 0.0)),
            "completion_tokens": float(raw.get("completion_tokens", 0.0)),
            "solved_tasks": int(raw.get("solved_tasks", 0)),
            "total_tasks": int(raw.get("total_tasks", 0)),
        }
    return summaries


def _load_result_sets(base_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    return {name: load_jsonl(base_dir / filename) for name, filename in RESULT_FILES.items()}


def build_objective_switch_cases(
    objective_records: List[Dict[str, Any]],
    audit_by_task: Dict[str, Dict[str, Any]],
    result_sets: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    indexes = {name: by_task(records) for name, records in result_sets.items()}
    cases = []
    for record in objective_records:
        if record.get("selected_source") == "baseline":
            continue
        task_id = str(record["task_id"])
        true_answer = normalize_option(record.get("true_answer"))
        baseline_prediction = normalize_option(record.get("baseline_prediction"))
        selected_prediction = normalize_option(record.get("predicted_answer"))
        baseline_correct = is_solved(baseline_prediction, true_answer)
        selected_correct = is_solved(selected_prediction, true_answer)
        if (not baseline_correct) and selected_correct:
            outcome = "fix"
        elif baseline_correct and (not selected_correct):
            outcome = "harm"
        else:
            outcome = "neutral"
        method_predictions = {}
        for name in [
            "ARG baseline",
            "PN router",
            "PN candidate",
            "PN conservative",
            "PN calibrated",
            "PN result ensemble",
        ]:
            method_predictions[name] = normalize_option(
                indexes.get(name, {}).get(task_id, {}).get("predicted_answer")
            )
        ranked = []
        for variant in record.get("ranked_variants") or []:
            ranked.append(
                {
                    "method": variant.get("method_key"),
                    "score": variant.get("score"),
                    "router_option": normalize_option(variant.get("router_option")),
                    "direct_majority": normalize_option(variant.get("direct_majority")),
                    "prediction": normalize_option(variant.get("predicted_answer")),
                    "has_prompt_node_graph": bool(variant.get("has_prompt_node_graph")),
                }
            )
        audit = audit_by_task.get(task_id, {})
        cases.append(
            {
                "task_id": task_id,
                "outcome": outcome,
                "audit_label": audit.get("clean_label", "unknown"),
                "gold_binding_status": audit.get("gold_binding_status", "unknown"),
                "rationale_issue": audit.get("rationale_issue", "unknown"),
                "true_answer": true_answer,
                "baseline_prediction": baseline_prediction,
                "selected_prediction": selected_prediction,
                "selected_source": record.get("selected_source"),
                "top_score": record.get("top_score"),
                "method_predictions": method_predictions,
                "ranked_variants": ranked,
                "question_short": " ".join(str(record.get("question", "")).split())[:220],
                "update2_boundary": (
                    "accuracy switch uses multi-view contract evidence, but this record has no explicit "
                    "PromptNode role in generated_graph/ranked_variants"
                    if not has_promptnode_graph_marker(record)
                    else "explicit PromptNode graph marker present"
                ),
            }
        )
    return cases


def build_tail34_report_payload(base_dir: str | Path = "experiment/aqua") -> Dict[str, Any]:
    base = Path(base_dir)
    result_sets = _load_result_sets(base)
    direct_costs = _load_direct_cost_summaries(base)
    audit_by_task = load_audit(base / "aqua_tail34_option_binding_audit.jsonl")
    baseline = result_sets["ARG baseline"]

    method_summaries: Dict[str, Dict[str, Any]] = {}
    for name in FULL_SYSTEM_PARTS:
        cost = direct_costs[name]
        method_summaries[name] = summarize_method(
            name,
            result_sets[name],
            baseline,
            audit_by_task,
            cost=cost["cost"],
            prompt_tokens=cost["prompt_tokens"],
            completion_tokens=cost["completion_tokens"],
            execution_scope="single run",
        )

    full_cost = build_full_system_cost(method_summaries)
    for name in ["PN result ensemble", "Objective-guided selector", "Margin-3 objective selector"]:
        method_summaries[name] = summarize_method(
            name,
            result_sets[name],
            baseline,
            audit_by_task,
            cost=full_cost["cost"],
            prompt_tokens=full_cost["prompt_tokens"],
            completion_tokens=full_cost["completion_tokens"],
            execution_scope=full_cost["execution_scope"],
        )

    baseline_cost = method_summaries["ARG baseline"]["cost"]
    baseline_solved = method_summaries["ARG baseline"]["solved"]
    for summary in method_summaries.values():
        delta = int(summary["delta_vs_baseline"])
        if delta > 0:
            summary["incremental_cost_per_extra_correct"] = (
                summary["cost"] - baseline_cost
            ) / delta
        else:
            summary["incremental_cost_per_extra_correct"] = None
        summary["solved_per_dollar"] = (
            summary["solved"] / summary["cost"] if summary["cost"] else None
        )
        summary["relative_cost_vs_arg"] = (
            summary["cost"] / baseline_cost if baseline_cost else None
        )
        summary["delta_solved_vs_arg"] = summary["solved"] - baseline_solved

    switch_cases = build_objective_switch_cases(
        result_sets["Objective-guided selector"],
        audit_by_task,
        result_sets,
    )
    promptnode_graph_hits = sum(
        summary["promptnode_graph_hit_count"] for summary in method_summaries.values()
    )

    return {
        "date": str(date.today()),
        "dataset": "AQuA tail34",
        "baseline": "ARG-Designer-compatible ARG baseline, gpt-4o-2024-08-06",
        "method_summaries": method_summaries,
        "full_system_cost": full_cost,
        "objective_switch_cases": switch_cases,
        "evidence_boundary": {
            "update2_compliance": "partial",
            "why_partial": (
                "R065 gives a positive held-out accuracy signal for multi-view contract/objective "
                "selection, but generated_graph/ranked_variants contain 0 explicit PromptNode graph "
                "markers on tail34. It validates the selector direction, not yet the full update2 "
                "train-time virtual-node graph policy."
            ),
            "promptnode_graph_hits_across_report": promptnode_graph_hits,
            "must_not_claim": [
                "Do not claim that R065 already trains PromptNode as a first-class virtual node.",
                "Do not claim general MAS improvement from one 34-task AQuA split.",
                "Do not hide the multi-view execution cost.",
            ],
            "next_required_for_sci_q2": [
                "Implement PromptNode as a first-class generated graph node with identity, edges, permissions, budget, and lifecycle labels.",
                "Train or distill a graph-policy/selector so the R065 signal is approximated without running all four PN views.",
                "Validate on MMLU STEM transfer or a larger AQuA held-out split with clean/noisy audit and cost normalization.",
            ],
        },
    }


def _format_float(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    return f"{float(value):.{digits}f}"


def render_markdown(payload: Dict[str, Any]) -> str:
    summaries = payload["method_summaries"]
    lines = [
        "# AQuA Tail34 SCI-Q2 Goal Evidence Report",
        "",
        f"**Date:** {payload['date']}",
        "",
        "## Goal Boundary",
        "",
        "PromptNode must be treated as a first-class virtual MAS graph node: identity type, structured content, connection edges, read/write/forward permissions, budget, and lifecycle actions. R065 is useful evidence, but only partial compliance with that design.",
        "",
        f"**Update2 compliance:** `{payload['evidence_boundary']['update2_compliance']}`",
        "",
        payload["evidence_boundary"]["why_partial"],
        "",
        "## Tail34 Result Table",
        "",
        "| Variant | Overall | Clean | Noisy/Amb. | Delta | Fix/Harm | Clean F/H | Switches | PN graph hits | Cost | Cost/correct | Relative cost |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in [
        "ARG baseline",
        "PN router",
        "PN candidate",
        "PN conservative",
        "PN calibrated",
        "PN result ensemble",
        "Objective-guided selector",
        "Margin-3 objective selector",
    ]:
        row = summaries[name]
        lines.append(
            "| {variant} | `{overall}` | `{clean}` | `{noisy}` | `{delta:+d}` | `{fix_harm}` | `{clean_fix_harm}` | `{switches}` | `{pn_hits}` | `${cost:.6f}` | `${cost_correct}` | `{relative}x` |".format(
                variant=name,
                overall=row["overall"],
                clean=row["clean"],
                noisy=row["noisy_or_ambiguous"],
                delta=int(row["delta_vs_baseline"]),
                fix_harm=row["fix_harm"],
                clean_fix_harm=row["clean_fix_harm"],
                switches=row["switches"],
                pn_hits=row["promptnode_graph_hits"],
                cost=float(row["cost"]),
                cost_correct=_format_float(row["cost_per_correct"], 4),
                relative=_format_float(row["relative_cost_vs_arg"], 2),
            )
        )

    lines.extend(
        [
            "",
            "## Cost-Normalized Reading",
            "",
            f"- Full multi-view execution cost: `${payload['full_system_cost']['cost']:.6f}` for 34 tasks.",
            "- Objective-guided selector and result ensemble are CPU-only after traces exist, but a deployable system must pay for baseline + four PN views unless we train/distill a cheaper graph policy.",
            f"- Objective-guided selector adds `+{summaries['Objective-guided selector']['delta_solved_vs_arg']}` solved tasks over ARG with incremental cost per extra correct `${_format_float(summaries['Objective-guided selector']['incremental_cost_per_extra_correct'], 4)}`.",
            "",
            "## Objective Switch Cases",
            "",
            "| Task | Audit | Outcome | Gold | ARG | Selected | Top score | Method predictions | Boundary |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for case in payload["objective_switch_cases"]:
        preds = ", ".join(f"{k}={v or '-'}" for k, v in case["method_predictions"].items())
        audit = f"{case['audit_label']}/{case['gold_binding_status']}/{case['rationale_issue']}"
        lines.append(
            "| {task} | {audit} | {outcome} | {gold} | {arg} | {selected} | {score} | {preds} | {boundary} |".format(
                task=case["task_id"],
                audit=audit,
                outcome=case["outcome"],
                gold=case["true_answer"],
                arg=case["baseline_prediction"],
                selected=case["selected_prediction"],
                score=case["top_score"],
                preds=preds,
                boundary=case["update2_boundary"],
            )
        )

    lines.extend(
        [
            "",
            "## Claims Allowed Now",
            "",
            "1. On AQuA tail34, multi-view objective-guided selection reaches `31/34` versus ARG `28/34`, with fix/harm `3/0` and clean fix/harm `1/0`.",
            "2. The gain is not only noisy-label exploitation: the audited clean split is `28/28`, including one clean fix and zero clean harms.",
            "3. The current positive signal is cost-heavy and only partially implements the update2 PromptNode design.",
            "",
            "## Claims Not Allowed Yet",
            "",
        ]
    )
    for claim in payload["evidence_boundary"]["must_not_claim"]:
        lines.append(f"- {claim}")
    lines.extend(["", "## Required Next Work", ""])
    for item in payload["evidence_boundary"]["next_required_for_sci_q2"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    directory = os.path.dirname(path_str(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def write_text(path: str | Path, text: str) -> None:
    directory = os.path.dirname(path_str(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build tail34 SCI-Q2 evidence and boundary report.")
    parser.add_argument("--base-dir", default=os.path.dirname(__file__))
    parser.add_argument(
        "--output-json",
        default=os.path.join(os.path.dirname(__file__), "res_logs/aqua_tail34_sci_q2_evidence_summary.json"),
    )
    parser.add_argument(
        "--output-md",
        default=os.path.join(os.path.dirname(__file__), "run_logs/aqua_tail34_sci_q2_evidence_report.md"),
    )
    args = parser.parse_args()

    payload = build_tail34_report_payload(args.base_dir)
    write_json(args.output_json, payload)
    write_text(args.output_md, render_markdown(payload))
    print(json.dumps({"output_json": args.output_json, "output_md": args.output_md}, indent=2))


if __name__ == "__main__":
    main()
