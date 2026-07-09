import argparse
import itertools
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r118_lightweight_objective_probe_replay"
CLAIM_BOUNDARY = "offline probe replay only; no new API, measured cost, or accuracy claim"

DEFAULT_OBJECTIVE_JSONL = "experiment/aqua/aqua_tail34_objective_guided_selector_results.jsonl"
DEFAULT_R109_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r109_objective_safety_rule_distillation_summary.json"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r118_lightweight_objective_probe_replay_summary.json"
)
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r118_lightweight_objective_probe_replay_report.md"

METHOD_ORDER = ["router", "candidate", "conservative", "calibrated"]
VALID_OPTIONS = {"A", "B", "C", "D", "E"}


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _normalize_option(value: Any) -> Optional[str]:
    if isinstance(value, str):
        option = value.strip().upper()
        if option in VALID_OPTIONS:
            return option
    return None


def _select_probe_prediction(
    baseline_prediction: Any,
    ranked_variants: Sequence[Dict[str, Any]],
) -> Tuple[Optional[str], str, int]:
    baseline = _normalize_option(baseline_prediction)
    if not ranked_variants:
        return baseline, "baseline", 0
    top_score = int(ranked_variants[0].get("score") or 0)
    if top_score < 1:
        return baseline, "baseline", top_score
    top_variants = [variant for variant in ranked_variants if int(variant.get("score") or 0) == top_score]
    top_options = {
        _normalize_option(variant.get("router_option")) or _normalize_option(variant.get("predicted_answer"))
        for variant in top_variants
    }
    top_options.discard(None)
    if len(top_options) != 1:
        return baseline, "baseline", top_score
    selected = next(iter(top_options))
    if selected == baseline:
        return baseline, "baseline", top_score
    return selected, "objective_top", top_score


def _proxy_action(policy_input: Dict[str, Any]) -> str:
    switch = (
        bool(policy_input["objective_prediction_differs_from_baseline"])
        and (
            int(policy_input["objective_top_score"]) >= 3
            or bool(policy_input["baseline_direct_votes_split"])
        )
    )
    return "switch_to_objective" if switch else "fallback_to_arg"


def _subset_ranked(record: Dict[str, Any], subset: Sequence[str]) -> List[Dict[str, Any]]:
    order = {method: index for index, method in enumerate(METHOD_ORDER)}
    return sorted(
        [
            variant
            for variant in record.get("ranked_variants") or []
            if variant.get("method_key") in subset
        ],
        key=lambda variant: (-int(variant.get("score") or 0), order.get(variant.get("method_key"), 99)),
    )


def _evaluate_subset(
    subset: Sequence[str],
    objective_by_task: Dict[str, Dict[str, Any]],
    target_rows: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    matches = 0
    switch_tasks: List[str] = []
    false_switch_tasks: List[str] = []
    missed_switch_tasks: List[str] = []
    for target in target_rows:
        task_id = target["task_id"]
        record = objective_by_task[task_id]
        ranked = _subset_ranked(record, subset)
        policy_input = dict(target["rule_input"])
        selected, source, top_score = _select_probe_prediction(
            policy_input["baseline_prediction"],
            ranked,
        )
        policy_input["objective_prediction"] = selected
        policy_input["objective_selected_source"] = source
        policy_input["objective_top_score"] = top_score
        policy_input["objective_prediction_differs_from_baseline"] = (
            selected != policy_input["baseline_prediction"]
        )
        proxy_action = _proxy_action(policy_input)
        target_action = target["target_action"]
        matches += int(proxy_action == target_action)
        if proxy_action == "switch_to_objective":
            switch_tasks.append(task_id)
        if proxy_action == "switch_to_objective" and target_action != "switch_to_objective":
            false_switch_tasks.append(task_id)
        if proxy_action != "switch_to_objective" and target_action == "switch_to_objective":
            missed_switch_tasks.append(task_id)
    return {
        "subset": list(subset),
        "view_count": len(subset),
        "target_agreement": f"{matches}/{len(target_rows)}",
        "target_agreement_count": matches,
        "switch_tasks": switch_tasks,
        "false_switch_tasks": false_switch_tasks,
        "missed_switch_tasks": missed_switch_tasks,
    }


def build_lightweight_objective_probe_replay_summary() -> Dict[str, Any]:
    objective_by_task = {row["task_id"]: row for row in _load_jsonl(DEFAULT_OBJECTIVE_JSONL)}
    target_rows = list(_load_json(DEFAULT_R109_SUMMARY_JSON)["rows"])
    subsets = [
        subset
        for size in (1, 2)
        for subset in itertools.combinations(METHOD_ORDER, size)
    ]
    results = [
        _evaluate_subset(subset, objective_by_task, target_rows)
        for subset in subsets
    ]
    successful = [
        result for result in results if result["target_agreement"] == f"{len(target_rows)}/{len(target_rows)}"
    ]
    one_view_success = [result for result in successful if result["view_count"] == 1]
    two_view_success = [result for result in successful if result["view_count"] == 2]
    best = sorted(successful, key=lambda result: (result["view_count"], result["subset"]))[0]
    return {
        "rule": RULE_NAME,
        "replay_only": True,
        "candidate_subset_count": len(results),
        "one_view_success_count": len(one_view_success),
        "two_view_success_count": len(two_view_success),
        "best_min_view_subset": best["subset"],
        "best_min_view_count": best["view_count"],
        "best_min_view_target_agreement": best["target_agreement"],
        "best_min_view_switch_tasks": best["switch_tasks"],
        "best_min_view_false_switch_tasks": best["false_switch_tasks"],
        "best_min_view_missed_switch_tasks": best["missed_switch_tasks"],
        "recommended_probe_protocol": "calibrated_single_view_probe",
        "api_result_ready": False,
        "subset_results": results,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "| `{subset}` | `{views}` | `{agreement}` | `{switches}` | `{false}` | `{missed}` |".format(
            subset=",".join(result["subset"]),
            views=result["view_count"],
            agreement=result["target_agreement"],
            switches=result["switch_tasks"],
            false=result["false_switch_tasks"],
            missed=result["missed_switch_tasks"],
        )
        for result in summary["subset_results"]
    ]
    return "\n".join(
        [
            "# R118 Lightweight Objective Probe Replay",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Replay only: `{summary['replay_only']}`",
            f"- Candidate subsets: `{summary['candidate_subset_count']}`",
            f"- One-view successes: `{summary['one_view_success_count']}`",
            f"- Two-view successes: `{summary['two_view_success_count']}`",
            f"- Best min-view subset: `{summary['best_min_view_subset']}`",
            f"- Best min-view target agreement: `{summary['best_min_view_target_agreement']}`",
            f"- Recommended probe protocol: `{summary['recommended_probe_protocol']}`",
            f"- API result ready: `{summary['api_result_ready']}`",
            "",
            "| Subset | Views | Agreement | Switches | False switches | Missed switches |",
            "| --- | ---: | ---: | --- | --- | --- |",
            *rows,
            "",
            "## Interpretation",
            "",
            "R118 shows that the calibrated view alone reproduces the frozen R109 objective-safety target "
            "actions in an offline replay. This supports making `calibrated_single_view_probe` the first "
            "R117 smoke candidate, but it is not a measured API result or cost claim.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay lightweight objective probe subsets.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_lightweight_objective_probe_replay_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R118 lightweight objective probe replay: "
        f"best={summary['best_min_view_subset']} "
        f"agreement={summary['best_min_view_target_agreement']}"
    )


if __name__ == "__main__":
    main()
