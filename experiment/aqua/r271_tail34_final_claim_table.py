from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Set

from experiment.aqua.r267_cost_safety_combined_selector import (
    BAD_TASKS,
    build_r267_summary,
    load_json,
    load_jsonl,
    normalize_label,
    write_json,
    write_text,
)


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_ARG_JSONL = os.path.join(SCRIPT_DIR, "aqua_tail34_arg_baseline_results.jsonl")
DEFAULT_R065_JSONL = os.path.join(SCRIPT_DIR, "aqua_tail34_objective_guided_selector_results.jsonl")
DEFAULT_R068_JSONL = os.path.join(SCRIPT_DIR, "aqua_tail34_r068_selective_multiview_results.jsonl")
DEFAULT_R068_SUMMARY = os.path.join(SCRIPT_DIR, "res_logs", "aqua_tail34_r068_selective_multiview_summary.json")
DEFAULT_R095_SUMMARY = os.path.join(SCRIPT_DIR, "res_logs", "aqua_tail34_r095_objective_safety_composed_summary.json")
DEFAULT_SUMMARY_JSON = os.path.join(SCRIPT_DIR, "res_logs", "aqua_tail34_r271_final_claim_table_summary.json")
DEFAULT_REPORT_MD = os.path.join(SCRIPT_DIR, "run_logs", "aqua_tail34_r271_final_claim_table.md")

FULL_MULTIVIEW_COST = 5.050805
ARG_COST = 0.93285


def _score(
    rows: Iterable[Dict[str, Any]],
    excluded: Set[str],
    corrected: Dict[str, str],
) -> str:
    kept = []
    for row in rows:
        task_id = str(row["task_id"])
        if task_id in excluded:
            continue
        pred = normalize_label(row.get("predicted_answer"))
        gold = normalize_label(corrected.get(task_id, row.get("true_answer")))
        kept.append(pred == gold)
    return f"{sum(kept)}/{len(kept)}"


def _r095_rows() -> List[Dict[str, Any]]:
    summary = load_json(DEFAULT_R095_SUMMARY)
    rows = []
    for row in summary["rows"]:
        rows.append(
            {
                "task_id": row["task_id"],
                "true_answer": row["true_answer"],
                "predicted_answer": row["safety_composed_prediction"],
            }
        )
    return rows


def _variant_scores(rows: List[Dict[str, Any]]) -> Dict[str, str]:
    return {
        "official": _score(rows, set(), {}),
        "audit_clean_exclude_59_139_228": _score(rows, BAD_TASKS, {}),
        "correct_task114": _score(rows, BAD_TASKS, {"task_114": "C"}),
        "exclude_task114": _score(rows, BAD_TASKS | {"task_114"}, {}),
    }


def build_r271_summary() -> Dict[str, Any]:
    r267 = build_r267_summary()
    r068_cost = round(load_json(DEFAULT_R068_SUMMARY)["cost_estimate"]["estimated_cost"], 6)
    variants = {
        "ARG": {
            **_variant_scores(load_jsonl(DEFAULT_ARG_JSONL)),
            "cost": round(ARG_COST, 6),
            "claim_role": "baseline",
        },
        "R065": {
            **_variant_scores(load_jsonl(DEFAULT_R065_JSONL)),
            "cost": round(FULL_MULTIVIEW_COST, 6),
            "claim_role": "highest official replay score, noisy task114 risk",
        },
        "R068": {
            **_variant_scores(load_jsonl(DEFAULT_R068_JSONL)),
            "cost": r068_cost,
            "claim_role": "cost-reduced replay retaining R065 score",
        },
        "R095": {
            **_variant_scores(_r095_rows()),
            "cost": round(FULL_MULTIVIEW_COST, 6),
            "claim_role": "safety-gated replay, not cost-reduced",
        },
        "R267": {
            "official": r267["official"]["accuracy"],
            "audit_clean_exclude_59_139_228": r267["exclude_59_139_228"]["accuracy"],
            "correct_task114": r267["exclude_59_139_228_correct_114"]["accuracy"],
            "exclude_task114": r267["exclude_59_139_228_114"]["accuracy"],
            "cost": r267["cost_estimate"]["estimated_cost"],
            "claim_role": "cost-reduced plus safety-gated replay",
        },
    }
    return {
        "run_id": "R271",
        "title": "Tail34 final official/audit-clean claim table",
        "claim_boundary": "paper_table_generation_only_no_new_api",
        "variants": variants,
        "recommended_main_text_claim": "official_plus_audit_clean_scope_limited",
        "recommended_wording": (
            "Report official and audit-clean columns side by side. Use R065/R068 for the official improvement signal and R095/R267 for the safety/audit-clean interpretation. Do not claim broad transfer superiority."
        ),
    }


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# R271 Tail34 Final Claim Table",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "| Variant | Official | Excl. 59/139/228 | Correct 114 | Excl. 114 | Cost | Role |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for name, row in summary["variants"].items():
        lines.append(
            f"| `{name}` | `{row['official']}` | `{row['audit_clean_exclude_59_139_228']}` | `{row['correct_task114']}` | `{row['exclude_task114']}` | `${row['cost']}` | {row['claim_role']} |"
        )
    lines.extend(["", summary["recommended_wording"], ""])
    return "\n".join(lines)


def run(
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_r271_summary()
    write_json(summary_json, summary)
    write_text(report_md, render_report(summary))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
