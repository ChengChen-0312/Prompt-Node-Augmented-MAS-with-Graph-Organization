import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Sequence


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.edge_prompt_repair_smoke_report import (  # noqa: E402
    _is_solved,
    _load_audit_labels,
    _load_jsonl,
    _ratio,
    write_jsonl,
)
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r147_tail34_frozen_selector_replay_and_expansion_protocol"
CLAIM_BOUNDARY = (
    "full-tail34 frozen-selector replay using R059 ARG baseline plus R146 switch API "
    "results; not a fresh integrated full run, transfer result, robustness proof, or "
    "SCI-readiness claim"
)

DEFAULT_TASK_SPLIT = "experiment/aqua/task_split_aqua_tail34.json"
DEFAULT_BASELINE_JSONL = "experiment/aqua/aqua_tail34_arg_baseline_results.jsonl"
DEFAULT_BASELINE_SUMMARY_JSONL = "experiment/aqua/res_logs/aqua_tail34_arg_baseline_summary.jsonl"
DEFAULT_R113_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r113_objective_safety_proxy_rule_summary.json"
DEFAULT_R126_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r126_clean_fix_graph_policy_selector_protocol_summary.json"
DEFAULT_R146_SMOKE_JSONL = "experiment/aqua/aqua_tail34_r146_calibrated_repair_smoke.jsonl"
DEFAULT_R146_SUMMARY = "experiment/aqua/res_logs/aqua_tail34_r146_calibrated_repair_smoke_summary.json"
DEFAULT_AUDIT_FILE = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r147_frozen_selector_replay.jsonl"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r147_frozen_selector_replay_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r147_frozen_selector_replay_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _last_jsonl(path: str) -> Dict[str, Any]:
    records = _load_jsonl(path)
    return records[-1] if records else {}


def _index_by_task(rows: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(row["task_id"]): row for row in rows}


def _fix_harm(rows: Sequence[Dict[str, Any]]) -> str:
    return _ratio(sum(1 for row in rows if row["fix"]), sum(1 for row in rows if row["harm"]))


def build_tail34_frozen_selector_replay_rows(
    task_split: str = DEFAULT_TASK_SPLIT,
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    r113_summary: str = DEFAULT_R113_SUMMARY,
    r146_smoke_jsonl: str = DEFAULT_R146_SMOKE_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
) -> List[Dict[str, Any]]:
    task_ids = [f"task_{idx}" for idx in _load_json(task_split)["test_indices"]]
    baseline = _index_by_task(_load_jsonl(baseline_jsonl))
    r113 = _load_json(r113_summary)
    switch_tasks = set(r113["frozen_tail34_switch_tasks"])
    switch_rows = _index_by_task(_load_jsonl(r146_smoke_jsonl))
    audit_labels = _load_audit_labels(audit_file)

    rows: List[Dict[str, Any]] = []
    for task_id in task_ids:
        base = baseline[task_id]
        switch = switch_rows.get(task_id) if task_id in switch_tasks else None
        selected_prediction = (
            switch["selected_prediction"] if switch else base["predicted_answer"]
        )
        truth = base["true_answer"]
        baseline_solved = _is_solved(base["predicted_answer"], truth)
        selected_solved = _is_solved(selected_prediction, truth)
        rows.append(
            {
                "task_id": task_id,
                "clean_label": audit_labels.get(task_id, ""),
                "baseline_prediction": base["predicted_answer"],
                "selected_prediction": selected_prediction,
                "true_answer": truth,
                "selected_source": (
                    "r146_calibrated_promptnode_switch" if switch else "r059_arg_fallback"
                ),
                "baseline_is_solved": baseline_solved,
                "selected_is_solved": selected_solved,
                "fix": (not baseline_solved) and selected_solved,
                "harm": baseline_solved and not selected_solved,
                "has_promptnode_graph": bool(switch and switch.get("has_promptnode_graph")),
                "has_update2_metadata": bool(switch and switch.get("has_update2_metadata")),
                "router_repair_option": (switch or {}).get("router_repair_option", ""),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_tail34_frozen_selector_replay_summary(
    task_split: str = DEFAULT_TASK_SPLIT,
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    baseline_summary_jsonl: str = DEFAULT_BASELINE_SUMMARY_JSONL,
    r113_summary: str = DEFAULT_R113_SUMMARY,
    r126_summary: str = DEFAULT_R126_SUMMARY,
    r146_smoke_jsonl: str = DEFAULT_R146_SMOKE_JSONL,
    r146_summary: str = DEFAULT_R146_SUMMARY,
    audit_file: str = DEFAULT_AUDIT_FILE,
) -> Dict[str, Any]:
    rows = build_tail34_frozen_selector_replay_rows(
        task_split=task_split,
        baseline_jsonl=baseline_jsonl,
        r113_summary=r113_summary,
        r146_smoke_jsonl=r146_smoke_jsonl,
        audit_file=audit_file,
    )
    r113 = _load_json(r113_summary)
    r126 = _load_json(r126_summary)
    r146 = _load_json(r146_summary)
    baseline_summary = _last_jsonl(baseline_summary_jsonl)
    switch_rows = [row for row in rows if row["selected_source"] != "r059_arg_fallback"]
    fallback_rows = [row for row in rows if row["selected_source"] == "r059_arg_fallback"]
    clean_rows = [row for row in rows if row.get("clean_label") == "clean"]
    noisy_rows = [row for row in rows if row.get("clean_label") != "clean"]
    baseline_correct = sum(row["baseline_is_solved"] for row in rows)
    selected_correct = sum(row["selected_is_solved"] for row in rows)
    baseline_cost = float(baseline_summary.get("cost") or 0.0)
    incremental_cost = float(r146.get("forced_cost") or 0.0)
    selected_cost = round(baseline_cost + incremental_cost, 6)

    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "full_tail34_replay_only": True,
        "no_new_api_run": True,
        "fresh_integrated_full_run": False,
        "total_tasks": len(rows),
        "baseline_accuracy": _ratio(baseline_correct, len(rows)),
        "selected_accuracy": _ratio(selected_correct, len(rows)),
        "baseline_accuracy_rate": round(baseline_correct / len(rows), 6),
        "selected_accuracy_rate": round(selected_correct / len(rows), 6),
        "switch_tasks": r113["frozen_tail34_switch_tasks"],
        "fallback_task_count": len(fallback_rows),
        "promptnode_graph_evidence_on_switches": _ratio(
            sum(1 for row in switch_rows if row["has_promptnode_graph"]), len(switch_rows)
        ),
        "switch_update2_metadata": _ratio(
            sum(1 for row in switch_rows if row["has_update2_metadata"]), len(switch_rows)
        ),
        "fix_harm": _fix_harm(rows),
        "clean_fix_harm": _fix_harm(clean_rows),
        "noisy_fix_harm": _fix_harm(noisy_rows),
        "selector_input_field_violations": int(
            r146.get("selector_input_field_violations") or 0
        ),
        "uses_tail34_training_source": bool(
            r113.get("uses_tail34_training_source")
            or r126.get("uses_tail34_training_source")
        ),
        "baseline_cost": round(baseline_cost, 6),
        "incremental_promptnode_cost": round(incremental_cost, 6),
        "selected_estimated_cost": selected_cost,
        "cost_delta_vs_baseline": round(incremental_cost, 6),
        "cost_ratio_vs_baseline": round(selected_cost / baseline_cost, 6),
        "baseline_correct_per_dollar": round(baseline_correct / baseline_cost, 6),
        "selected_correct_per_dollar": round(selected_correct / selected_cost, 6),
        "r146_smoke_gate_passed": bool(r146.get("smoke_gate_passed")),
        "full_tail34_replay_claim_supported": True,
        "broad_api_allowed_next": False,
        "next_protocol": "r148_tail34_replay_statistical_audit_and_transfer_preflight",
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{label}` | `{source}` | `{base}` | `{sel}` | `{truth}` | `{fix}` | `{harm}` |".format(
            task=row["task_id"],
            label=row.get("clean_label", ""),
            source=row["selected_source"],
            base=row["baseline_prediction"],
            sel=row["selected_prediction"],
            truth=row["true_answer"],
            fix=row["fix"],
            harm=row["harm"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R147 Tail34 Frozen-Selector Replay and Expansion Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Full tail34 replay only: `{summary['full_tail34_replay_only']}`",
            f"- No new API run: `{summary['no_new_api_run']}`",
            f"- Fresh integrated full run: `{summary['fresh_integrated_full_run']}`",
            f"- Baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- Selected accuracy: `{summary['selected_accuracy']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback task count: `{summary['fallback_task_count']}`",
            f"- PN graph evidence on switches: `{summary['promptnode_graph_evidence_on_switches']}`",
            f"- Switch update2 metadata: `{summary['switch_update2_metadata']}`",
            f"- Fix/harm: `{summary['fix_harm']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            f"- Uses tail34 training source: `{summary['uses_tail34_training_source']}`",
            f"- Baseline cost: `${summary['baseline_cost']:.6f}`",
            f"- Incremental PromptNode cost: `${summary['incremental_promptnode_cost']:.6f}`",
            f"- Selected estimated cost: `${summary['selected_estimated_cost']:.6f}`",
            f"- Cost ratio vs baseline: `{summary['cost_ratio_vs_baseline']}`",
            f"- Baseline correct per dollar: `{summary['baseline_correct_per_dollar']}`",
            f"- Selected correct per dollar: `{summary['selected_correct_per_dollar']}`",
            f"- R146 smoke gate passed: `{summary['r146_smoke_gate_passed']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "| Task | Label | Source | Baseline | Selected | Truth | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R147 gives the first full-tail34 replay for the frozen selector: ARG fallback "
            "is retained on 32 tasks, and the two pre-registered switch tasks use R146 "
            "calibrated PromptNode outputs. This supports a replay-level tail34 improvement "
            "boundary (`30/34` vs `28/34`) but still requires statistical audit, transfer "
            "preflight, and eventually broader validation before paper-level claims.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build R147 tail34 frozen-selector replay and expansion protocol."
    )
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_tail34_frozen_selector_replay_rows()
    summary = build_tail34_frozen_selector_replay_summary()
    write_jsonl(args.output_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R147 tail34 frozen-selector replay: "
        f"selected={summary['selected_accuracy']} clean={summary['clean_fix_harm']} "
        f"cost=${summary['selected_estimated_cost']:.6f} broad={summary['broad_api_allowed_next']}"
    )


if __name__ == "__main__":
    main()
