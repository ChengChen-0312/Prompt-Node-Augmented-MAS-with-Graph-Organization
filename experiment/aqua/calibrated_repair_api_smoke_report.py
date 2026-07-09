import argparse
import os
import sys
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.edge_prompt_repair_forwarding_smoke_report import (  # noqa: E402
    _float_or_zero,
)
from experiment.aqua.edge_prompt_repair_smoke_report import (  # noqa: E402
    DEFAULT_AUDIT_FILE,
    DEFAULT_BASELINE_JSONL,
    DEFAULT_R127_PLAN_JSONL,
    _index_by_task,
    build_edge_prompt_repair_smoke_rows,
    build_edge_prompt_repair_smoke_summary,
    write_jsonl,
)
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from mas_framework.agents.final_decision import (  # noqa: E402
    EDGE_REPAIR_MIN_CONFIDENCE,
    calibrate_edge_prompt_repair_confidence,
    extract_edge_prompt_repair_candidates,
    select_calibrated_edge_prompt_repair_answer,
)


RULE_NAME = "r146_bounded_calibrated_repair_api_smoke"
DECISION_METHOD = "CalibratedEdgePromptRepairContractFinalRefer"
CLAIM_BOUNDARY = (
    "same-four-task bounded calibrated repair API smoke; clean repair is supported "
    "on the regression gate, but broad held-out evaluation, transfer, robustness, "
    "and SCI-readiness remain unsupported"
)

DEFAULT_FORCED_JSONL = "experiment/aqua/aqua_tail34_r146_calibrated_repair_switch_results.jsonl"
DEFAULT_FORCED_SUMMARY_JSONL = (
    "experiment/aqua/res_logs/aqua_tail34_r146_calibrated_repair_switch_summary.jsonl"
)
DEFAULT_OUTPUT_JSONL = "experiment/aqua/aqua_tail34_r146_calibrated_repair_smoke.jsonl"
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r146_calibrated_repair_smoke_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r146_calibrated_repair_smoke_report.md"
)


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _record_to_spatial_info(record: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    spatial_info: Dict[str, Dict[str, str]] = {}
    for output in record.get("agent_outputs") or []:
        node_id = str(output.get("node"))
        spatial_info[node_id] = {
            "role": str(output.get("role") or ""),
            "output": "\n".join(str(item) for item in output.get("outputs") or []),
        }
    return spatial_info


def _calibrated_task250_diagnostics(forced_jsonl: str) -> Dict[str, Any]:
    forced_records = _index_by_task(forced_jsonl)
    task250_record = forced_records["task_250"]
    spatial_info = _record_to_spatial_info(task250_record)
    candidates = [
        candidate
        for candidate in extract_edge_prompt_repair_candidates(spatial_info)
        if candidate.get("repair_option") in {"A", "B", "C", "D", "E"}
    ]
    task250_candidate = candidates[0] if candidates else {}
    calibrated_confidence = (
        calibrate_edge_prompt_repair_confidence(task250_candidate, spatial_info)
        if task250_candidate
        else 0.0
    )
    selected_repair = select_calibrated_edge_prompt_repair_answer(spatial_info)
    return {
        "task250_calibrated_repair_confidence": calibrated_confidence,
        "task250_calibrated_repair_gate_passed": selected_repair == "E",
    }


def _with_r146_diagnostics(rows: List[Dict[str, Any]], forced_jsonl: str) -> List[Dict[str, Any]]:
    diagnostics = _calibrated_task250_diagnostics(forced_jsonl)
    enriched = []
    for row in rows:
        row = dict(row)
        if row["selected_source"].startswith("rank5_"):
            row["selected_source"] = f"rank5_{DECISION_METHOD}"
        row["claim_boundary"] = CLAIM_BOUNDARY
        if row["task_id"] == "task_250":
            row.update(diagnostics)
        else:
            row["task250_calibrated_repair_confidence"] = ""
            row["task250_calibrated_repair_gate_passed"] = False
        enriched.append(row)
    return enriched


def build_calibrated_repair_api_smoke_rows(
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    forced_jsonl: str = DEFAULT_FORCED_JSONL,
    r127_plan_jsonl: str = DEFAULT_R127_PLAN_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
) -> List[Dict[str, Any]]:
    rows = build_edge_prompt_repair_smoke_rows(
        baseline_jsonl=baseline_jsonl,
        forced_jsonl=forced_jsonl,
        r127_plan_jsonl=r127_plan_jsonl,
        audit_file=audit_file,
    )
    return _with_r146_diagnostics(rows, forced_jsonl)


def build_calibrated_repair_api_smoke_summary(
    baseline_jsonl: str = DEFAULT_BASELINE_JSONL,
    forced_jsonl: str = DEFAULT_FORCED_JSONL,
    r127_plan_jsonl: str = DEFAULT_R127_PLAN_JSONL,
    audit_file: str = DEFAULT_AUDIT_FILE,
    forced_summary_jsonl: str = DEFAULT_FORCED_SUMMARY_JSONL,
) -> Dict[str, Any]:
    summary = build_edge_prompt_repair_smoke_summary(
        baseline_jsonl=baseline_jsonl,
        forced_jsonl=forced_jsonl,
        r127_plan_jsonl=r127_plan_jsonl,
        audit_file=audit_file,
        forced_summary_jsonl=forced_summary_jsonl,
    )
    rows = _with_r146_diagnostics(summary["rows"], forced_jsonl)
    task250 = next(row for row in rows if row["task_id"] == "task_250")
    summary.update(
        {
            "rule": RULE_NAME,
            "decision_method": DECISION_METHOD,
            "rows": rows,
            "task250_router_repair_option": task250["router_repair_option"],
            "task250_router_repair_binding_status": task250[
                "router_repair_binding_status"
            ],
            "task250_router_repair_confidence": _float_or_zero(
                task250["router_repair_confidence"]
            ),
            "task250_calibrated_repair_confidence": task250[
                "task250_calibrated_repair_confidence"
            ],
            "repair_min_confidence": EDGE_REPAIR_MIN_CONFIDENCE,
            "task250_calibrated_repair_gate_passed": task250[
                "task250_calibrated_repair_gate_passed"
            ],
            "broad_api_allowed_next": False,
            "next_protocol": "r147_bounded_smoke_result_to_claim_and_expansion_protocol",
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{label}` | `{source}` | `{base}` | `{sel}` | `{truth}` | `{repair}` | `{raw}` | `{cal}` | `{fix}` | `{harm}` |".format(
            task=row["task_id"],
            label=row.get("clean_label", ""),
            source=row["selected_source"],
            base=row["baseline_prediction"],
            sel=row["selected_prediction"],
            truth=row["true_answer"],
            repair=row["router_repair_option"],
            raw=row["router_repair_confidence"],
            cal=row.get("task250_calibrated_repair_confidence", ""),
            fix=row["fix"],
            harm=row["harm"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R146 Bounded Calibrated Repair API Smoke",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Decision method: `{summary['decision_method']}`",
            f"- Baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- Selected accuracy: `{summary['selected_accuracy']}`",
            f"- Switch tasks: `{summary['switch_tasks']}`",
            f"- Fallback tasks: `{summary['fallback_tasks']}`",
            f"- PN graph evidence on switches: `{summary['promptnode_graph_evidence_on_switches']}`",
            f"- Switch update2 metadata: `{summary['switch_update2_metadata']}`",
            f"- Fix/harm: `{summary['fix_harm']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            f"- Switch router repair fields present: `{summary['switch_router_repair_fields_present']}`",
            f"- Switch router repair option non-none: `{summary['switch_router_repair_option_non_none']}`",
            f"- task250 verifier repair candidate present: `{summary['task250_verifier_repair_candidate_present']}`",
            f"- task250 router repair forwarded: `{summary['task250_router_repair_forwarded']}`",
            f"- Verifier-router repair forwarding gap: `{summary['verifier_router_repair_forwarding_gap']}`",
            f"- task250 router repair option: `{summary['task250_router_repair_option']}`",
            f"- task250 raw router repair confidence: `{summary['task250_router_repair_confidence']}`",
            f"- task250 calibrated repair confidence: `{summary['task250_calibrated_repair_confidence']}`",
            f"- Repair minimum confidence: `{summary['repair_min_confidence']}`",
            f"- task250 calibrated repair gate passed: `{summary['task250_calibrated_repair_gate_passed']}`",
            f"- Forced cost: `${summary['forced_cost']:.6f}`",
            f"- Integrity gate passed: `{summary['integrity_gate_passed']}`",
            f"- Smoke gate passed: `{summary['smoke_gate_passed']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "| Task | Label | Source | Baseline | Selected | Truth | Router repair | Raw repair confidence | Calibrated confidence | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R146 is the first fresh bounded API smoke where the calibrated repair final gate "
            "recovers clean `task_250` while preserving the fallback clean guards. This supports "
            "a same-four-task smoke claim only. It does not authorize broad tail34, transfer, "
            "robustness, or SCI-readiness claims until a separate result-to-claim and expansion "
            "protocol freezes the next evaluation scope.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize R146 bounded calibrated repair API smoke."
    )
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_calibrated_repair_api_smoke_rows()
    summary = build_calibrated_repair_api_smoke_summary()
    write_jsonl(args.output_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R146 calibrated repair API smoke report: "
        f"selected={summary['selected_accuracy']} clean={summary['clean_fix_harm']} "
        f"smoke={summary['smoke_gate_passed']} broad={summary['broad_api_allowed_next']}"
    )


if __name__ == "__main__":
    main()
