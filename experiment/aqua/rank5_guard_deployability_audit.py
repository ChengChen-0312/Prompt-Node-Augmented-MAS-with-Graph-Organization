import argparse
import json
import os
import re
import sys
from collections import defaultdict
from typing import Any, Dict, List, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r108_rank5_guard_deployability_audit"
CLAIM_BOUNDARY = "feature audit only; no accuracy or new selector claim"

DEFAULT_R095_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r095_objective_safety_composed_summary.json"
DEFAULT_R106_RESULTS_JSONL = "experiment/aqua/aqua_tail34_r106_rank5_regression_smoke_results.jsonl"
DEFAULT_R107_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r107_objective_safety_rank5_guard_summary.json"
DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r108_rank5_guard_deployability_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r108_rank5_guard_deployability_report.md"

FORBIDDEN_SELECTOR_FIELDS = {
    "task_id",
    "true_answer",
    "is_solved",
    "baseline_is_solved",
    "rank5_is_solved",
    "guarded_is_solved",
    "clean_label",
    "gold_binding_status",
    "audit_label",
    "rationale_issue",
}


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _extract_contract_field(text: str, field: str) -> str:
    match = re.search(rf"{field}:\s*([A-Z_/]+)", text or "", flags=re.I)
    return match.group(1).upper() if match else ""


def _router_text(record: Dict[str, Any]) -> str:
    for output in record.get("agent_outputs") or []:
        if output.get("role") == "PN_Router":
            return "\n".join(str(item) for item in output.get("outputs") or [])
    return ""


def _selected_candidate(record: Dict[str, Any]) -> Dict[str, Any]:
    candidates = record.get("candidate_graphs") or []
    selected_index = int(record.get("selected_candidate_index") or 0)
    if 0 <= selected_index < len(candidates):
        return candidates[selected_index]
    return {}


def _r095_index() -> Dict[str, Dict[str, Any]]:
    return {row["task_id"]: row for row in _load_json(DEFAULT_R095_SUMMARY_JSON)["rows"]}


def _r107_action_index() -> Dict[str, str]:
    return {row["task_id"]: row["action"] for row in _load_json(DEFAULT_R107_SUMMARY_JSON)["rows"]}


def _label_normalized_rank5_features(record: Dict[str, Any], baseline_prediction: str) -> Dict[str, Any]:
    router = _router_text(record)
    selected = _selected_candidate(record)
    return {
        "selected_rank": int(selected.get("rank") or 0),
        "graph_signature": selected.get("graph_signature") or "",
        "router_binding_status": _extract_contract_field(router, "BINDING_STATUS"),
        "router_supported_option_kind": (
            "none" if _extract_contract_field(router, "SUPPORTED_OPTION") in {"", "NONE"} else "specific"
        ),
        "rank5_prediction_differs_from_baseline": record["predicted_answer"] != baseline_prediction,
    }


def _objective_features(r095_row: Dict[str, Any]) -> Dict[str, Any]:
    features = r095_row["decision_features"]
    return {
        "baseline_direct_votes_split": bool(features["baseline_direct_votes_split"]),
        "objective_prediction_differs_from_baseline": bool(
            features["objective_prediction_differs_from_baseline"]
        ),
        "objective_top_score": int(features["objective_top_score"]),
    }


def _feature_key(features: Dict[str, Any]) -> Tuple[Tuple[str, Any], ...]:
    return tuple(sorted(features.items()))


def build_deployability_rows() -> List[Dict[str, Any]]:
    r095 = _r095_index()
    r107_actions = _r107_action_index()
    rows = []
    for record in _load_jsonl(DEFAULT_R106_RESULTS_JSONL):
        task_id = record["task_id"]
        base = r095[task_id]
        single_features = _label_normalized_rank5_features(record, base["baseline_prediction"])
        objective_features = _objective_features(base)
        rows.append(
            {
                "task_id": task_id,
                "rank5_prediction": record["predicted_answer"],
                "baseline_prediction": base["baseline_prediction"],
                "r107_action": r107_actions[task_id],
                "single_template_features": single_features,
                "objective_features": objective_features,
                "true_answer": base["true_answer"],
                "rank5_is_solved": bool(record["is_solved"]),
                "clean_label": base["clean_label"],
            }
        )
    return rows


def _input_violation_count(rows: List[Dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        for source in ("single_template_features", "objective_features"):
            count += sum(1 for key in row[source] if key in FORBIDDEN_SELECTOR_FIELDS)
    return count


def build_deployability_summary() -> Dict[str, Any]:
    rows = build_deployability_rows()
    groups: Dict[Tuple[Tuple[str, Any], ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[_feature_key(row["single_template_features"])].append(row)

    ambiguous_groups = [
        group
        for group in groups.values()
        if len(group) > 1 and len({row["r107_action"] for row in group}) > 1
    ]
    ambiguous_tasks = [row["task_id"] for group in ambiguous_groups for row in group]
    objective_feature_keys = {
        _feature_key(row["objective_features"])
        for group in ambiguous_groups
        for row in group
    }
    objective_separates = bool(ambiguous_groups) and len(objective_feature_keys) > 1

    return {
        "rule": RULE_NAME,
        "num_tasks": len(rows),
        "ambiguous_single_template_groups": len(ambiguous_groups),
        "ambiguous_no_exact_diff_tasks": ambiguous_tasks,
        "objective_features_separate_ambiguous_tasks": objective_separates,
        "single_template_guard_sufficient": False if ambiguous_groups else True,
        "selector_input_field_violations": _input_violation_count(rows),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{action}` | `{base}` | `{rank5}` | `{binding}` | `{support}` | `{diff}` | `{obj_diff}` | `{obj_score}` |".format(
            task=row["task_id"],
            action=row["r107_action"],
            base=row["baseline_prediction"],
            rank5=row["rank5_prediction"],
            binding=row["single_template_features"]["router_binding_status"],
            support=row["single_template_features"]["router_supported_option_kind"],
            diff=row["single_template_features"]["rank5_prediction_differs_from_baseline"],
            obj_diff=row["objective_features"]["objective_prediction_differs_from_baseline"],
            obj_score=row["objective_features"]["objective_top_score"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R108 Rank5 Guard Deployability Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Ambiguous single-template groups: `{summary['ambiguous_single_template_groups']}`",
            f"- Ambiguous no-exact/diff tasks: `{summary['ambiguous_no_exact_diff_tasks']}`",
            f"- Objective features separate ambiguous tasks: `{summary['objective_features_separate_ambiguous_tasks']}`",
            f"- Single-template guard sufficient: `{summary['single_template_guard_sufficient']}`",
            f"- Selector input field violations: `{summary['selector_input_field_violations']}`",
            "",
            "| Task | R107 action | ARG | Rank5 | Rank5 binding | Supported option kind | Rank5 differs | Objective differs | Objective score |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "`task_8` and `task_250` share the same label-normalized single-template pattern: "
            "rank5 differs from ARG, emits `NO_EXACT_OPTION`, and uses the same rank5 graph. "
            "They require different actions, so the current evidence does not justify a cheap "
            "single-template guard. The separating signal comes from the objective-safety features, "
            "which means the next step must train or approximate that objective rather than trusting "
            "rank5 traces alone.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit deployability of the R107 rank5 guard.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_deployability_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R108 rank5 guard deployability audit: "
        f"ambiguous_groups={summary['ambiguous_single_template_groups']} "
        f"single_template_guard_sufficient={summary['single_template_guard_sufficient']}"
    )


if __name__ == "__main__":
    main()
