import argparse
import datetime
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r129_task250_router_none_failure_diagnosis"
CLAIM_BOUNDARY = (
    "diagnosis only; no API run, no new accuracy result, and task250 rank5 historical "
    "success is not a clean router-supported fix"
)

TASK_ID = "task_250"
DEFAULT_RUNS: Sequence[Tuple[str, str]] = (
    ("R128", "experiment/aqua/aqua_tail34_r128_rank5_high_fanin_switch_results.jsonl"),
    ("R100", "experiment/aqua/aqua_tail34_r100_forced_template_rank5_task250_results.jsonl"),
    ("R106", "experiment/aqua/aqua_tail34_r106_rank5_regression_smoke_results.jsonl"),
)
DEFAULT_OUTPUT_JSONL = (
    "experiment/aqua/aqua_tail34_r129_task250_router_none_failure_diagnosis.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r129_task250_router_none_failure_diagnosis_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r129_task250_router_none_failure_diagnosis_report.md"
)


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_task_record(path: str, task_id: str = TASK_ID) -> Dict[str, Any]:
    for row in _load_jsonl(path):
        if row.get("task_id") == task_id:
            return row
    raise ValueError(f"Missing {task_id} in {path}")


def _normalize_option(value: Any) -> str:
    match = re.search(r"\b([A-E])\b", str(value or "").upper())
    if match:
        return match.group(1)
    match = re.search(r"[A-E]", str(value or "").upper())
    return match.group(0) if match else ""


def _extract_contract_field(text: str, field: str) -> str:
    match = re.search(rf"{field}:\s*([A-Z0-9_/]+)", text or "", flags=re.I)
    return match.group(1).upper() if match else ""


def _router_output(record: Dict[str, Any]) -> str:
    for output in record.get("agent_outputs") or []:
        if output.get("role") == "PN_Router":
            return "\n".join(str(item) for item in output.get("outputs") or [])
    return ""


def _selected_rank(record: Dict[str, Any]) -> int:
    index = int(record.get("selected_candidate_index") or 0)
    candidates = record.get("candidate_graphs") or []
    if 0 <= index < len(candidates):
        return int(candidates[index].get("rank") or index + 1)
    return index + 1


def _is_router_none_no_exact(router_option: str, binding_status: str) -> bool:
    return router_option == "NONE" and binding_status == "NO_EXACT_OPTION"


def _is_nearest_choice_coercion(raw_response: str) -> bool:
    text = (raw_response or "").lower()
    return "closest" in text or "nearest" in text or "best-supported option" in text


def _run_row(run_name: str, result_path: str) -> Dict[str, Any]:
    record = _load_task_record(result_path)
    router_text = _router_output(record)
    router_supported_option = _extract_contract_field(router_text, "SUPPORTED_OPTION")
    router_binding_status = _extract_contract_field(router_text, "BINDING_STATUS")
    predicted_answer = _normalize_option(record.get("predicted_answer"))
    true_answer = _normalize_option(record.get("true_answer"))
    router_none_no_exact = _is_router_none_no_exact(router_supported_option, router_binding_status)
    final_layer_selected_option_after_router_none = bool(predicted_answer) and router_none_no_exact
    return {
        "run_name": run_name,
        "task_id": record.get("task_id"),
        "result_path": result_path,
        "predicted_answer": predicted_answer,
        "true_answer": true_answer,
        "is_solved": predicted_answer == true_answer,
        "selected_rank": _selected_rank(record),
        "router_supported_option": router_supported_option,
        "router_binding_status": router_binding_status,
        "router_none_no_exact": router_none_no_exact,
        "final_layer_selected_option_after_router_none": (
            final_layer_selected_option_after_router_none
        ),
        "nearest_choice_or_best_supported_text": _is_nearest_choice_coercion(
            record.get("raw_response") or ""
        ),
        "router_text": router_text,
        "raw_response_excerpt": str(record.get("raw_response") or "")[:1000],
        "generated_graph": record.get("generated_graph") or {},
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _ratio(count: int, total: int) -> str:
    return f"{int(count)}/{int(total)}"


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_task250_router_none_failure_diagnosis(
    runs: Sequence[Tuple[str, str]] = DEFAULT_RUNS,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows = [_run_row(run_name, result_path) for run_name, result_path in runs]
    by_run = {row["run_name"]: row for row in rows}
    historical_success_rows = [
        row for row in rows if row["run_name"] in {"R100", "R106"} and row["is_solved"]
    ]
    historical_success_is_nearest_choice_coercion = bool(historical_success_rows) and all(
        row["final_layer_selected_option_after_router_none"]
        and row["nearest_choice_or_best_supported_text"]
        for row in historical_success_rows
    )
    router_contract_supported_clean_fix = any(
        row["is_solved"]
        and row["router_supported_option"] == row["predicted_answer"]
        and row["router_binding_status"] == "EXACT_MATCH"
        for row in historical_success_rows
    )
    same_rank_runs = len({row["selected_rank"] for row in rows}) == 1
    inconsistent_outcomes_under_same_rank = len({row["predicted_answer"] for row in rows}) > 1
    rank_selection_sufficient = not (
        same_rank_runs
        and inconsistent_outcomes_under_same_rank
        and historical_success_is_nearest_choice_coercion
    )

    total = len(rows)
    summary = {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "diagnosis_only": True,
        "no_api_run": True,
        "task_id": TASK_ID,
        "compared_runs": [row["run_name"] for row in rows],
        "r128_prediction": by_run["R128"]["predicted_answer"],
        "r100_prediction": by_run["R100"]["predicted_answer"],
        "r106_prediction": by_run["R106"]["predicted_answer"],
        "r128_is_solved": by_run["R128"]["is_solved"],
        "r100_is_solved": by_run["R100"]["is_solved"],
        "r106_is_solved": by_run["R106"]["is_solved"],
        "router_none_no_exact_runs": _ratio(
            sum(1 for row in rows if row["router_none_no_exact"]), total
        ),
        "final_option_after_router_none_runs": _ratio(
            sum(1 for row in rows if row["final_layer_selected_option_after_router_none"]),
            total,
        ),
        "selected_ranks": {row["run_name"]: row["selected_rank"] for row in rows},
        "router_contract_supported_clean_fix": router_contract_supported_clean_fix,
        "historical_success_is_nearest_choice_coercion": (
            historical_success_is_nearest_choice_coercion
        ),
        "r128_final_layer_overrode_router_none": by_run["R128"][
            "final_layer_selected_option_after_router_none"
        ],
        "rank_selection_sufficient": rank_selection_sufficient,
        "failure_mode": (
            "final aggregation may select a forced option even after PN_Router abstains "
            "with NONE/NO_EXACT_OPTION"
        ),
        "next_required_protocol": "deterministic_none_guard_or_exact_option_repair_before_api",
        "broad_api_allowed_next": False,
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    return rows, summary


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{run}` | `{rank}` | `{router}` | `{binding}` | `{pred}` | `{gold}` | `{solved}` | `{coercion}` |".format(
            run=row["run_name"],
            rank=row["selected_rank"],
            router=row["router_supported_option"],
            binding=row["router_binding_status"],
            pred=row["predicted_answer"],
            gold=row["true_answer"],
            solved=row["is_solved"],
            coercion=row["nearest_choice_or_best_supported_text"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R129 Task250 Router-NONE Failure Diagnosis",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Compared runs: `{summary['compared_runs']}`",
            f"- Router NONE/NO_EXACT_OPTION runs: `{summary['router_none_no_exact_runs']}`",
            f"- Final option after router NONE runs: `{summary['final_option_after_router_none_runs']}`",
            f"- R128 prediction: `{summary['r128_prediction']}`",
            f"- R100 prediction: `{summary['r100_prediction']}`",
            f"- R106 prediction: `{summary['r106_prediction']}`",
            f"- Router-contract-supported clean fix: `{summary['router_contract_supported_clean_fix']}`",
            f"- Historical success is nearest-choice coercion: `{summary['historical_success_is_nearest_choice_coercion']}`",
            f"- Rank selection sufficient: `{summary['rank_selection_sufficient']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next required protocol: `{summary['next_required_protocol']}`",
            "",
            "| Run | Rank | Router option | Binding | Prediction | Gold | Solved | Nearest/best-supported text |",
            "| --- | ---: | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "All three rank-5 executions for `task_250` end with the same terminal router contract: "
            "`SUPPORTED_OPTION: NONE` and `BINDING_STATUS: NO_EXACT_OPTION`. The two historical "
            "successes, R100 and R106, therefore cannot be claimed as clean router-supported fixes: "
            "their final layer selected `E` after the router abstained. R128 selected `A` under the "
            "same abstention boundary. The next method step must make the final decision deterministic "
            "under router abstention or add an exact-option repair stage before any broader API run.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose task_250 router NONE failures.")
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows, summary = build_task250_router_none_failure_diagnosis()
    write_jsonl(args.output_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built task250 router-NONE diagnosis: "
        f"none_no_exact={summary['router_none_no_exact_runs']} "
        f"rank_sufficient={summary['rank_selection_sufficient']} "
        f"broad_api_allowed_next={summary['broad_api_allowed_next']}"
    )


if __name__ == "__main__":
    main()
