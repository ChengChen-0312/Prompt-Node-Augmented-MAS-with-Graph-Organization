import argparse
import os
import sys
from typing import Any, Dict, Iterable, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.edge_prompt_repair_smoke_report import (  # noqa: E402
    DEFAULT_AUDIT_FILE,
    DEFAULT_BASELINE_JSONL,
    DEFAULT_R127_PLAN_JSONL,
    build_edge_prompt_repair_smoke_rows,
    build_edge_prompt_repair_smoke_summary,
    write_jsonl,
)
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from mas_framework.agents.final_decision import EDGE_REPAIR_MIN_CONFIDENCE  # noqa: E402


RULE_NAME = "r139_edge_prompt_repair_forwarding_smoke"
CLAIM_BOUNDARY = (
    "same-four-task repair-forwarding smoke; forwarding is fixed but clean recovery, "
    "broad held-out evaluation, transfer, robustness, and SCI-readiness remain unsupported"
)

DEFAULT_FORCED_JSONL = (
    "experiment/aqua/aqua_tail34_r139_edge_prompt_repair_forwarding_switch_results.jsonl"
)
DEFAULT_FORCED_SUMMARY_JSONL = (
    "experiment/aqua/res_logs/"
    "aqua_tail34_r139_edge_prompt_repair_forwarding_switch_summary.jsonl"
)
DEFAULT_OUTPUT_JSONL = (
    "experiment/aqua/aqua_tail34_r139_edge_prompt_repair_forwarding_smoke.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r139_edge_prompt_repair_forwarding_smoke_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r139_edge_prompt_repair_forwarding_smoke_report.md"
)


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _float_or_zero(value: Any) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


def _with_forwarding_diagnostics(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched = []
    for row in rows:
        confidence = _float_or_zero(row.get("router_repair_confidence"))
        row = dict(row)
        row["router_repair_confidence_float"] = confidence
        row["repair_confidence_gate_passed"] = confidence >= EDGE_REPAIR_MIN_CONFIDENCE
        row["claim_boundary"] = CLAIM_BOUNDARY
        enriched.append(row)
    return enriched


def build_edge_prompt_repair_forwarding_smoke_rows(
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
    return _with_forwarding_diagnostics(rows)


def build_edge_prompt_repair_forwarding_smoke_summary(
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
    rows = _with_forwarding_diagnostics(summary["rows"])
    task250 = next(row for row in rows if row["task_id"] == "task_250")
    confidence = task250["router_repair_confidence_float"]
    summary.update(
        {
            "rule": RULE_NAME,
            "rows": rows,
            "task250_router_repair_option": task250["router_repair_option"],
            "task250_router_repair_binding_status": task250[
                "router_repair_binding_status"
            ],
            "task250_router_repair_confidence": confidence,
            "repair_min_confidence": EDGE_REPAIR_MIN_CONFIDENCE,
            "task250_repair_confidence_gate_passed": (
                confidence >= EDGE_REPAIR_MIN_CONFIDENCE
            ),
            "task250_repair_forwarded_but_rejected_low_confidence": (
                task250["router_repair_option_non_none"]
                and confidence < EDGE_REPAIR_MIN_CONFIDENCE
            ),
            "broad_api_allowed_next": False,
            "next_protocol": "r140_goal_audit_then_repair_confidence_calibration_protocol",
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{label}` | `{source}` | `{base}` | `{sel}` | `{truth}` | `{repair}` | `{conf}` | `{gate}` | `{fix}` | `{harm}` |".format(
            task=row["task_id"],
            label=row.get("clean_label", ""),
            source=row["selected_source"],
            base=row["baseline_prediction"],
            sel=row["selected_prediction"],
            truth=row["true_answer"],
            repair=row["router_repair_option"],
            conf=row["router_repair_confidence"],
            gate=row["repair_confidence_gate_passed"],
            fix=row["fix"],
            harm=row["harm"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R139 Edge-Prompt Repair-Forwarding Smoke",
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
            "- task250 router repair binding status: "
            f"`{summary['task250_router_repair_binding_status']}`",
            f"- task250 router repair confidence: `{summary['task250_router_repair_confidence']}`",
            f"- Repair minimum confidence: `{summary['repair_min_confidence']}`",
            "- task250 repair confidence gate passed: "
            f"`{summary['task250_repair_confidence_gate_passed']}`",
            "- task250 repair forwarded but rejected for low confidence: "
            f"`{summary['task250_repair_forwarded_but_rejected_low_confidence']}`",
            f"- Forced cost: `${summary['forced_cost']:.6f}`",
            f"- Integrity gate passed: `{summary['integrity_gate_passed']}`",
            f"- Smoke gate passed: `{summary['smoke_gate_passed']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "| Task | Label | Source | Baseline | Selected | Truth | Router repair | Repair confidence | Gate passed | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R139 fixes the R137 Verifier-to-Router forwarding gap: task250 now carries "
            "`REPAIR_OPTION: E` with `NUMERIC_NEAREST_WITH_TYPO_CHECK`. The final repair "
            "gate still rejects it because the router confidence is `0.50`, below the "
            f"`{EDGE_REPAIR_MIN_CONFIDENCE:.2f}` threshold. This preserves conservatism but "
            "does not pass the clean recovery gate. The next step is the scheduled R140 "
            "goal audit, then a calibration protocol if the goal remains aligned.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize R139 edge-prompt repair-forwarding smoke."
    )
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_edge_prompt_repair_forwarding_smoke_rows()
    summary = build_edge_prompt_repair_forwarding_smoke_summary()
    write_jsonl(args.output_jsonl, rows)
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R139 edge-prompt repair-forwarding smoke report: "
        f"selected={summary['selected_accuracy']} forwarded={summary['task250_router_repair_forwarded']} "
        f"gate={summary['task250_repair_confidence_gate_passed']}"
    )


if __name__ == "__main__":
    main()
