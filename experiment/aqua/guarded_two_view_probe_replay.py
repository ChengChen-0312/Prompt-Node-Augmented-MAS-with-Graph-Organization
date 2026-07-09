import argparse
import json
import os
import sys
from typing import Any, Dict, List, Sequence


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.contract_ablation_analysis import load_audit_labels  # noqa: E402
from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.offline_utility_selector import normalize_option  # noqa: E402
from experiment.aqua.selective_multiview_trigger import ratio_text, write_jsonl  # noqa: E402


RULE_NAME = "r122_guarded_two_view_probe_replay"
CLAIM_BOUNDARY = "guarded replay over existing traces; no new API or accuracy improvement claim"

DEFAULT_OBJECTIVE_JSONL = "experiment/aqua/aqua_tail34_objective_guided_selector_results.jsonl"
DEFAULT_AUDIT_FILE = "experiment/aqua/aqua_tail34_option_binding_audit.jsonl"
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r122_guarded_two_view_probe_replay.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r122_guarded_two_view_probe_replay_summary.json"
)
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r122_guarded_two_view_probe_replay_report.md"


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _has_update2_evidence(variant: Dict[str, Any]) -> bool:
    return bool(variant.get("has_prompt_node_graph")) or int(
        variant.get("strong_router_contract_count") or 0
    ) > 0


def _record_has_update2_evidence(record: Dict[str, Any]) -> bool:
    return any(_has_update2_evidence(variant) for variant in record.get("ranked_variants") or [])


def _top_selected_variants(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked = list(record.get("ranked_variants") or [])
    if not ranked:
        return []
    top_score = ranked[0].get("score")
    selected = normalize_option(record.get("predicted_answer"))
    variants = []
    for variant in ranked:
        if variant.get("score") != top_score:
            continue
        option = normalize_option(variant.get("router_option")) or normalize_option(
            variant.get("predicted_answer")
        )
        if option == selected:
            variants.append(variant)
    return variants


def _switch_allowed(record: Dict[str, Any]) -> bool:
    if record.get("selected_source") == "baseline":
        return False
    selected_variants = _top_selected_variants(record)
    if not selected_variants:
        return False
    has_evidence = any(_has_update2_evidence(variant) for variant in selected_variants)
    selected_methods = {variant.get("method_key") for variant in selected_variants}
    two_view_agreement = len(selected_methods) >= 2
    return bool(has_evidence and two_view_agreement)


def _is_solved(prediction: Any, true_answer: Any) -> bool:
    return normalize_option(prediction) == normalize_option(true_answer)


def build_guarded_rows(
    objective_jsonl: str = DEFAULT_OBJECTIVE_JSONL,
) -> List[Dict[str, Any]]:
    rows = []
    for record in _load_jsonl(objective_jsonl):
        baseline_prediction = normalize_option(record.get("baseline_prediction"))
        objective_prediction = normalize_option(record.get("predicted_answer"))
        switch_allowed = _switch_allowed(record)
        guarded_prediction = objective_prediction if switch_allowed else baseline_prediction
        true_answer = normalize_option(record.get("true_answer"))
        rows.append(
            {
                "task_id": record["task_id"],
                "true_answer": true_answer,
                "baseline_prediction": baseline_prediction,
                "objective_prediction": objective_prediction,
                "guarded_prediction": guarded_prediction,
                "objective_selected_source": record.get("selected_source"),
                "guarded_selected_source": "guarded_probe" if switch_allowed else "baseline",
                "objective_is_solved": _is_solved(objective_prediction, true_answer),
                "baseline_is_solved": _is_solved(baseline_prediction, true_answer),
                "guarded_is_solved": _is_solved(guarded_prediction, true_answer),
                "switch_allowed": switch_allowed,
                "has_update2_evidence": _record_has_update2_evidence(record),
                "top_selected_variants": _top_selected_variants(record),
            }
        )
    return rows


def _fix_harm(rows: Sequence[Dict[str, Any]], selected_key: str) -> str:
    fixes = sum(
        1
        for row in rows
        if not row["baseline_is_solved"] and row[selected_key]
    )
    harms = sum(
        1
        for row in rows
        if row["baseline_is_solved"] and not row[selected_key]
    )
    return f"{fixes}/{harms}"


def build_guarded_two_view_probe_replay_summary(
    objective_jsonl: str = DEFAULT_OBJECTIVE_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
) -> Dict[str, Any]:
    source_records = _load_jsonl(objective_jsonl)
    rows = build_guarded_rows(objective_jsonl)
    audit_labels = load_audit_labels([_repo_path(audit_file)])
    clean_rows = [row for row in rows if audit_labels.get(row["task_id"]) == "clean"]
    promptnode_graph_rows = sum(
        1
        for record in source_records
        if any(variant.get("has_prompt_node_graph") for variant in record.get("ranked_variants") or [])
    )
    strong_contract_rows = sum(
        1
        for record in source_records
        if any(
            int(variant.get("strong_router_contract_count") or 0) > 0
            for variant in record.get("ranked_variants") or []
        )
    )
    total = len(rows)
    objective_switch_tasks = [
        row["task_id"] for row in rows if row["objective_selected_source"] != "baseline"
    ]
    guarded_switch_tasks = [
        row["task_id"] for row in rows if row["guarded_selected_source"] != "baseline"
    ]
    return {
        "rule": RULE_NAME,
        "replay_only": True,
        "source_jsonl": objective_jsonl,
        "total_tasks": total,
        "baseline_accuracy": ratio_text(sum(row["baseline_is_solved"] for row in rows), total),
        "objective_accuracy": ratio_text(sum(row["objective_is_solved"] for row in rows), total),
        "guarded_accuracy": ratio_text(sum(row["guarded_is_solved"] for row in rows), total),
        "objective_switch_tasks": objective_switch_tasks,
        "guarded_switch_tasks": guarded_switch_tasks,
        "guarded_fix_harm": _fix_harm(rows, "guarded_is_solved"),
        "guarded_clean_fix_harm": _fix_harm(clean_rows, "guarded_is_solved"),
        "promptnode_graph_evidence_rows": ratio_text(promptnode_graph_rows, total),
        "strong_router_contract_rows": ratio_text(strong_contract_rows, total),
        "blocks_all_objective_switches": bool(objective_switch_tasks) and not guarded_switch_tasks,
        "update2_evidence_ready": promptnode_graph_rows > 0 and strong_contract_rows > 0,
        "broad_api_allowed_next": False,
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{base}` | `{obj}` | `{guarded}` | `{truth}` | `{source}` | `{allowed}` | `{evidence}` |".format(
            task=row["task_id"],
            base=row["baseline_prediction"],
            obj=row["objective_prediction"],
            guarded=row["guarded_prediction"],
            truth=row["true_answer"],
            source=row["objective_selected_source"],
            allowed=row["switch_allowed"],
            evidence=row["has_update2_evidence"],
        )
        for row in summary["rows"]
        if row["objective_selected_source"] != "baseline" or row["switch_allowed"]
    ]
    if not table_rows:
        table_rows.append("| none | - | - | - | - | - | - | - |")
    return "\n".join(
        [
            "# R122 Guarded Two-View Probe Replay",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Replay only: `{summary['replay_only']}`",
            f"- Total tasks: `{summary['total_tasks']}`",
            f"- Baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- Objective accuracy: `{summary['objective_accuracy']}`",
            f"- Guarded accuracy: `{summary['guarded_accuracy']}`",
            f"- Objective switch tasks: `{summary['objective_switch_tasks']}`",
            f"- Guarded switch tasks: `{summary['guarded_switch_tasks']}`",
            f"- Guarded Fix/Harm: `{summary['guarded_fix_harm']}`",
            f"- Guarded Clean Fix/Harm: `{summary['guarded_clean_fix_harm']}`",
            f"- PromptNode graph evidence rows: `{summary['promptnode_graph_evidence_rows']}`",
            f"- Strong router-contract rows: `{summary['strong_router_contract_rows']}`",
            f"- Blocks all objective switches: `{summary['blocks_all_objective_switches']}`",
            f"- Update2 evidence ready: `{summary['update2_evidence_ready']}`",
            "",
            "| Task | ARG | Objective | Guarded | Truth | Objective source | Switch allowed | Update2 evidence |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R122 shows that the strict R121 update2 guard blocks the existing objective switches because "
            "the stored objective traces do not contain explicit PromptNode graph or strong router-contract evidence. "
            "This is a necessary negative boundary: the next positive method must produce first-class PromptNode "
            "evidence prospectively, not only replay direct-vote support.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay R121 guarded probe over existing traces.")
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_guarded_two_view_probe_replay_summary()
    write_jsonl(_repo_path(args.output_jsonl), summary["rows"])
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R122 guarded two-view replay: "
        f"guarded={summary['guarded_accuracy']} switches={summary['guarded_switch_tasks']}"
    )


if __name__ == "__main__":
    main()
