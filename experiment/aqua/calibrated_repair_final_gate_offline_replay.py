import argparse
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402
from experiment.aqua.repair_confidence_calibration_offline_export import (  # noqa: E402
    calibrate_repair_confidence,
)
from mas_framework.agents.final_decision import EDGE_REPAIR_MIN_CONFIDENCE  # noqa: E402


RULE_NAME = "r143_calibrated_repair_final_gate_offline_replay"
CLAIM_BOUNDARY = (
    "offline replay over R139 traces only; no API, production final-gate change, "
    "transfer, robustness, or SCI-readiness claim"
)

DEFAULT_R139_SUMMARY = (
    "experiment/aqua/res_logs/aqua_tail34_r139_edge_prompt_repair_forwarding_smoke_summary.json"
)
DEFAULT_OUTPUT_JSONL = (
    "experiment/aqua/aqua_tail34_r143_calibrated_repair_final_gate_offline_replay.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r143_calibrated_repair_final_gate_offline_replay_summary.json"
)
DEFAULT_REPORT_MD = (
    "experiment/aqua/run_logs/aqua_tail34_r143_calibrated_repair_final_gate_offline_replay_report.md"
)


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_option(value: Any) -> str:
    value = str(value or "").strip()
    if value in {"A", "B", "C", "D", "E"}:
        return value
    match = re.search(r"\b([A-E])\b", value.upper())
    return match.group(1) if match else value


def _is_solved(prediction: Any, truth: Any) -> bool:
    return _normalize_option(prediction) == _normalize_option(truth)


def _ratio(count: int, total: int) -> str:
    return f"{int(count)}/{int(total)}"


def _fix_harm(rows: List[Dict[str, Any]]) -> str:
    return _ratio(sum(1 for row in rows if row["fix"]), sum(1 for row in rows if row["harm"]))


def _write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _calibration_features(row: Dict[str, Any]) -> Dict[str, Any]:
    raw_distance = row.get("router_repair_distance_ratio")
    try:
        distance = 1.0 if raw_distance in {"", None} else float(raw_distance)
    except (TypeError, ValueError):
        distance = 1.0
    return {
        "repair_binding_status": row.get("router_repair_binding_status"),
        "repair_distance_ratio": distance,
        "repair_confidence_text_bucket": "moderate",
        "verifier_router_repair_agreement": bool(row.get("router_repair_option_non_none")),
        "direct_majority_contradiction": False,
        "option_text_exactness": bool(row.get("router_repair_option_non_none")),
        "candidate_source_count": 1 if row.get("router_repair_option_non_none") else 0,
        "numeric_distance_bucket": "tiny" if distance <= 0.0001 else "large",
    }


def build_calibrated_replay_rows(r139_summary: str = DEFAULT_R139_SUMMARY) -> List[Dict[str, Any]]:
    r139 = _load_json(r139_summary)
    replay_rows = []
    for row in r139["rows"]:
        calibrated_prediction = row["selected_prediction"]
        calibrated_confidence = 0.0
        repair_used = False
        if row.get("router_repair_option_non_none"):
            calibrated_confidence = calibrate_repair_confidence(_calibration_features(row))
            if calibrated_confidence >= EDGE_REPAIR_MIN_CONFIDENCE:
                calibrated_prediction = row["router_repair_option"]
                repair_used = True
        baseline_solved = _is_solved(row["baseline_prediction"], row["true_answer"])
        calibrated_solved = _is_solved(calibrated_prediction, row["true_answer"])
        replay_rows.append(
            {
                "task_id": row["task_id"],
                "clean_label": row.get("clean_label", ""),
                "baseline_prediction": row["baseline_prediction"],
                "r139_selected_prediction": row["selected_prediction"],
                "calibrated_prediction": calibrated_prediction,
                "true_answer": row["true_answer"],
                "router_repair_option": row.get("router_repair_option", ""),
                "calibrated_repair_confidence": calibrated_confidence,
                "repair_used": repair_used,
                "baseline_is_solved": baseline_solved,
                "calibrated_is_solved": calibrated_solved,
                "fix": (not baseline_solved) and calibrated_solved,
                "harm": baseline_solved and not calibrated_solved,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return replay_rows


def build_calibrated_repair_final_gate_offline_replay(
    r139_summary: str = DEFAULT_R139_SUMMARY,
) -> Dict[str, Any]:
    r139 = _load_json(r139_summary)
    rows = build_calibrated_replay_rows(r139_summary)
    clean_rows = [row for row in rows if row.get("clean_label") == "clean"]
    noisy_rows = [row for row in rows if row.get("clean_label") != "clean"]
    task250 = next(row for row in rows if row["task_id"] == "task_250")
    calibrated_accuracy = _ratio(sum(row["calibrated_is_solved"] for row in rows), len(rows))
    clean_harm_guard_passed = all(
        not row["harm"] for row in rows if row["task_id"] in {"task_8", "task_188"}
    )
    return {
        "rule": RULE_NAME,
        "offline_replay_only": True,
        "no_api_run": True,
        "uses_tail34_training_source": False,
        "baseline_accuracy": r139.get("baseline_accuracy"),
        "r139_selected_accuracy": r139.get("selected_accuracy"),
        "calibrated_selected_accuracy": calibrated_accuracy,
        "clean_fix_harm": _fix_harm(clean_rows),
        "noisy_fix_harm": _fix_harm(noisy_rows),
        "task250_calibrated_prediction": task250["calibrated_prediction"],
        "task250_calibrated_confidence": task250["calibrated_repair_confidence"],
        "task250_repair_used": bool(task250["repair_used"]),
        "clean_harm_guard_passed": clean_harm_guard_passed,
        "same_four_task_gate_offline_passed": (
            calibrated_accuracy == "4/4"
            and _fix_harm(clean_rows) == "1/0"
            and clean_harm_guard_passed
        ),
        "broad_api_allowed_next": False,
        "next_protocol": "calibrated_repair_final_gate_implementation_presmoke",
        "claim_boundary": CLAIM_BOUNDARY,
        "rows": rows,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{task}` | `{label}` | `{base}` | `{r139}` | `{cal}` | `{truth}` | `{conf}` | `{fix}` | `{harm}` |".format(
            task=row["task_id"],
            label=row.get("clean_label", ""),
            base=row["baseline_prediction"],
            r139=row["r139_selected_prediction"],
            cal=row["calibrated_prediction"],
            truth=row["true_answer"],
            conf=row["calibrated_repair_confidence"],
            fix=row["fix"],
            harm=row["harm"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R143 Calibrated Repair Final-Gate Offline Replay",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Offline replay only: `{summary['offline_replay_only']}`",
            f"- No API run: `{summary['no_api_run']}`",
            f"- Uses tail34 training source: `{summary['uses_tail34_training_source']}`",
            f"- Baseline accuracy: `{summary['baseline_accuracy']}`",
            f"- R139 selected accuracy: `{summary['r139_selected_accuracy']}`",
            f"- Calibrated selected accuracy: `{summary['calibrated_selected_accuracy']}`",
            f"- Clean fix/harm: `{summary['clean_fix_harm']}`",
            f"- Noisy fix/harm: `{summary['noisy_fix_harm']}`",
            f"- task250 calibrated prediction: `{summary['task250_calibrated_prediction']}`",
            f"- task250 calibrated confidence: `{summary['task250_calibrated_confidence']}`",
            f"- Clean harm guard passed: `{summary['clean_harm_guard_passed']}`",
            f"- Same-four-task gate offline passed: `{summary['same_four_task_gate_offline_passed']}`",
            f"- Broad API allowed next: `{summary['broad_api_allowed_next']}`",
            f"- Next protocol: `{summary['next_protocol']}`",
            "",
            "| Task | Label | Baseline | R139 Selected | Calibrated | Truth | Calibrated Confidence | Fix | Harm |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "R143 is an offline replay over existing R139 traces. It suggests the calibrated "
            "repair gate can recover task250 without harming the clean guards, but it is not "
            "a fresh API result and does not change the production final decision method.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write R143 calibrated repair final-gate offline replay."
    )
    parser.add_argument("--output-jsonl", default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_calibrated_repair_final_gate_offline_replay()
    _write_jsonl(args.output_jsonl, summary["rows"])
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R143 calibrated repair offline replay: "
        f"calibrated={summary['calibrated_selected_accuracy']} "
        f"clean={summary['clean_fix_harm']} broad={summary['broad_api_allowed_next']}"
    )


if __name__ == "__main__":
    main()
