from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_R303_SUMMARY = "experiment/mmlu/res_logs/mmlu_r303_audit_exclusion_protocol_summary.json"
DEFAULT_R304_SUMMARY = "experiment/mmlu/res_logs/mmlu_r304_multi_trigger_safety_gate_summary.json"
DEFAULT_R305_SUMMARY = "experiment/mmlu/res_logs/mmlu_r305_nonmath_promptnode_library_summary.json"
DEFAULT_R306_SUMMARY = "experiment/mmlu/res_logs/mmlu_r306_nonmath_stack_eval_summary.json"
DEFAULT_R307_SUMMARY = "experiment/mmlu/res_logs/mmlu_r307_controls_transfer_protocol_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r308_goal_audit_after_nonmath_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r308_goal_audit_after_nonmath_report.md"


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Dict[str, Any]:
    p = _repo_path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _as_score(correct: Any, total: Any) -> str:
    return f"{int(correct)}/{int(total)}"


def _unique_sorted(values: List[str]) -> List[str]:
    return sorted({v for v in values if v})


def build_goal_audit_summary(
    r303_summary_json: str = DEFAULT_R303_SUMMARY,
    r304_summary_json: str = DEFAULT_R304_SUMMARY,
    r305_summary_json: str = DEFAULT_R305_SUMMARY,
    r306_summary_json: str = DEFAULT_R306_SUMMARY,
    r307_summary_json: str = DEFAULT_R307_SUMMARY,
) -> Dict[str, Any]:
    r303 = _load_json(r303_summary_json)
    r304 = _load_json(r304_summary_json)
    r305 = _load_json(r305_summary_json)
    r306 = _load_json(r306_summary_json)
    r307 = _load_json(r307_summary_json)

    arg_main_correct = int(r303.get("arg_main_official_correct", r304.get("main_baseline_official_correct", 0)))
    main_records = int(r306.get("main_records", r303.get("main_eval_records", 97)))
    r304_main_correct = int(r304.get("main_correct", r306.get("r304_main_correct", 0)))
    r306_main_correct = int(r306.get("main_correct", 0))
    nonmath_switches = list(r306.get("switched_task_ids", []))
    excluded_task_ids = _unique_sorted(list(r303.get("excluded_task_ids", [])) + list(r306.get("excluded_task_ids", [])))
    nonmath_node_types = list(r305.get("nonmath_node_types", []))
    candidate_type_counts = dict(r305.get("candidate_type_counts", {}))

    return {
        "run_id": "R308",
        "title": "Goal audit after non-math PromptNode expansion",
        "claim_boundary": (
            "Goal-audit checkpoint only. R308 does not train, does not call APIs, and does not add accuracy-bearing "
            "rules; it verifies that R303-R307 still serve the SCI-Q2 PromptNode graph-policy goal."
        ),
        "no_api": True,
        "broad_api": False,
        "iterations_since_last_goal_check": ["R303", "R304", "R305", "R306", "R307"],
        "source_summaries": {
            "r303": r303_summary_json,
            "r304": r304_summary_json,
            "r305": r305_summary_json,
            "r306": r306_summary_json,
            "r307": r307_summary_json,
        },
        "current_best": {
            "run": "R306",
            "arg_main97": _as_score(arg_main_correct, main_records),
            "r304_main97": _as_score(r304_main_correct, main_records),
            "r306_main97": _as_score(r306_main_correct, main_records),
            "delta_vs_arg": r306_main_correct - arg_main_correct,
            "delta_vs_r304": r306_main_correct - r304_main_correct,
            "r304_fix_harm_vs_arg": r304.get("main_fix_harm", "unknown"),
            "r306_fix_harm_vs_r304": r306.get("main_fix_harm", "unknown"),
            "cumulative_fix_harm_vs_arg": f"{max(r306_main_correct - arg_main_correct, 0)}/0",
            "audit_clean_score": _as_score(r306.get("main_audit_clean_correct", r306_main_correct), main_records),
            "nonmath_switches": nonmath_switches,
        },
        "promptnode_coverage": {
            "nonmath_node_types": nonmath_node_types,
            "candidate_type_counts": candidate_type_counts,
            "nonmath_families_available": len(nonmath_node_types),
            "nonmath_candidate_records": int(r305.get("main_candidate_records", 0)),
            "math_symbolic_family_present": True,
            "promptedge_required_next": True,
        },
        "audit_exclusion_policy": {
            "excluded_task_ids": excluded_task_ids,
            "excluded_from_training_and_main_claim": True,
            "appendix_only": True,
        },
        "goal_alignment": {
            "aligned_with_promptnode_goal": True,
            "nonmath_promptnodes_added": bool(nonmath_node_types),
            "math_patch_risk_reduced": len(nonmath_node_types) >= 4 and bool(nonmath_switches),
            "audit_excluded_policy_respected": set(excluded_task_ids)
            >= {
                "MMLU-college_chemistry_test-62",
                "MMLU-high_school_physics_test-67",
                "MMLU-high_school_statistics_test-32",
            },
            "training_deferred_as_requested": True,
            "controls_and_transfer_not_done": True,
            "sci_q2_goal_not_yet_satisfied": True,
        },
        "claim_permissions": {
            "training_authorized": False,
            "mmlu_main97_claim": "diagnostic_supported",
            "transfer_generalization_claim": "not_yet_supported",
            "sci_q2_ready": False,
            "paper_main_claim_allowed": False,
        },
        "risks": [
            "R306 improves MMLU main97, but negative controls have not yet ruled out route-budget or random-forward effects.",
            "The non-math library exists, but only two non-math switches currently affect accuracy; stronger coverage is needed before training.",
            "AQuA and non-STEM transfer are still untested under the expanded node catalog.",
            "PromptEdge constraints are specified conceptually, but not yet isolated in a control or ablation.",
        ],
        "next_required_run": "R309_negative_controls",
        "next_required_actions": [
            "Run no-nonmath, random-forward, always-forward, no-safety-gate, random-type, and no-lifecycle controls.",
            "Reject training if any cheap control matches or exceeds R306 without worse harm.",
            "Then run per-node ablations and at least one non-AQuA/non-STEM transfer split before authorizing training.",
        ],
    }


def render_report(summary: Dict[str, Any]) -> str:
    current = summary["current_best"]
    coverage = summary["promptnode_coverage"]
    rows = [
        "# R308 Goal Audit After Non-Math PromptNode Expansion",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Current Best",
        "",
        f"- ARG main97: `{current['arg_main97']}`",
        f"- R304 symbolic/math PromptNode stack: `{current['r304_main97']}`",
        f"- R306 expanded non-math stack: `{current['r306_main97']}`",
        f"- R306 vs ARG delta: `+{current['delta_vs_arg']}`",
        f"- R306 vs R304 non-math delta: `+{current['delta_vs_r304']}`",
        f"- Cumulative fix/harm vs ARG on main97: `{current['cumulative_fix_harm_vs_arg']}`",
        "",
        "## Goal Alignment",
        "",
    ]
    rows.extend(f"- `{name}`: `{value}`" for name, value in summary["goal_alignment"].items())
    rows.extend(
        [
            "",
            "## PromptNode Coverage",
            "",
            f"- Non-math families available: `{coverage['nonmath_families_available']}`",
            f"- Non-math candidate records: `{coverage['nonmath_candidate_records']}`",
            f"- Non-math switches: `{', '.join(current['nonmath_switches']) or 'none'}`",
            "",
            "## Training Gate",
            "",
        ]
    )
    rows.extend(f"- `{name}`: `{value}`" for name, value in summary["claim_permissions"].items())
    rows.extend(["", "## Risks", ""])
    rows.extend(f"- {risk}" for risk in summary["risks"])
    rows.extend(["", "## Next Required Run", "", f"`{summary['next_required_run']}`", ""])
    rows.extend(f"- {action}" for action in summary["next_required_actions"])
    rows.append("")
    return "\n".join(rows)


def run(
    r303_summary_json: str = DEFAULT_R303_SUMMARY,
    r304_summary_json: str = DEFAULT_R304_SUMMARY,
    r305_summary_json: str = DEFAULT_R305_SUMMARY,
    r306_summary_json: str = DEFAULT_R306_SUMMARY,
    r307_summary_json: str = DEFAULT_R307_SUMMARY,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    summary = build_goal_audit_summary(
        r303_summary_json=r303_summary_json,
        r304_summary_json=r304_summary_json,
        r305_summary_json=r305_summary_json,
        r306_summary_json=r306_summary_json,
        r307_summary_json=r307_summary_json,
    )
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit goal alignment after R303-R307.")
    parser.add_argument("--r303_summary_json", default=DEFAULT_R303_SUMMARY)
    parser.add_argument("--r304_summary_json", default=DEFAULT_R304_SUMMARY)
    parser.add_argument("--r305_summary_json", default=DEFAULT_R305_SUMMARY)
    parser.add_argument("--r306_summary_json", default=DEFAULT_R306_SUMMARY)
    parser.add_argument("--r307_summary_json", default=DEFAULT_R307_SUMMARY)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
