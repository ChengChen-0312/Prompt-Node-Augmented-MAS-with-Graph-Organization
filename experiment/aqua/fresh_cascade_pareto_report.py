import argparse
import datetime
import json
import os
import sys
from typing import Any, Dict, List, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_RUNS = [
    (
        "R069",
        "fresh integrated four-view selective PromptNode",
        "experiment/aqua/res_logs/aqua_tail34_r069_integrated_selective_multiview_summary.json",
    ),
    (
        "R072",
        "fresh integrated cascade PromptNode",
        "experiment/aqua/res_logs/aqua_tail34_r072_integrated_cascade_summary.json",
    ),
    (
        "R074",
        "fresh integrated surgical cascade PromptNode",
        "experiment/aqua/res_logs/aqua_tail34_r074_surgical_cascade_summary.json",
    ),
]
RULE_NAME = "r075_fresh_cascade_pareto_report"


def load_json(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Dict[str, Any]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: str, text: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _absolute(path: str) -> str:
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(REPO_ROOT, path))


def _count_from_ratio(value: Optional[str]) -> int:
    if not value or "/" not in value:
        return 0
    return int(value.split("/", 1)[0])


def _row(run_id: str, description: str, summary_path: str) -> Dict[str, Any]:
    summary = load_json(_absolute(summary_path))
    return {
        "run_id": run_id,
        "description": description,
        "summary_path": summary_path,
        "overall": summary["overall"],
        "solved_tasks": int(summary.get("solved_tasks", _count_from_ratio(summary["overall"]))),
        "baseline": summary["baseline"],
        "baseline_solved_tasks": int(
            summary.get("baseline_solved_tasks", _count_from_ratio(summary["baseline"]))
        ),
        "delta_vs_baseline": int(summary.get("delta_vs_baseline", 0)),
        "clean": summary.get("clean"),
        "clean_fix_harm": summary.get("clean_fix_harm"),
        "clean_fixes": _count_from_ratio(summary.get("clean_fix_harm")),
        "noisy_fix_harm": summary.get("noisy_fix_harm"),
        "fix_harm": summary.get("fix_harm"),
        "fix_tasks": sorted(summary.get("fix_tasks", [])),
        "harm_tasks": sorted(summary.get("harm_tasks", [])),
        "switch_tasks": sorted(summary.get("switch_tasks", [])),
        "multiview_run": summary.get("multiview_run"),
        "view_calls": summary.get("view_calls"),
        "cost": round(float(summary.get("cost", 0.0)), 6),
        "trigger_policy": summary.get("trigger_policy"),
    }


def _accuracy_cost_frontier(rows: List[Dict[str, Any]]) -> List[str]:
    frontier = []
    for row in rows:
        dominated = False
        for other in rows:
            if other is row:
                continue
            if (
                other["solved_tasks"] >= row["solved_tasks"]
                and other["cost"] <= row["cost"]
                and (
                    other["solved_tasks"] > row["solved_tasks"]
                    or other["cost"] < row["cost"]
                )
            ):
                dominated = True
                break
        if not dominated:
            frontier.append(row["run_id"])
    return frontier


def _clean_mechanism_frontier(rows: List[Dict[str, Any]]) -> List[str]:
    frontier = []
    for row in rows:
        dominated = False
        for other in rows:
            if other is row:
                continue
            if (
                other["clean_fixes"] >= row["clean_fixes"]
                and other["cost"] <= row["cost"]
                and (
                    other["clean_fixes"] > row["clean_fixes"]
                    or other["cost"] < row["cost"]
                )
            ):
                dominated = True
                break
        if not dominated:
            frontier.append(row["run_id"])
    return frontier


def build_fresh_pareto_payload() -> Dict[str, Any]:
    rows = [_row(run_id, description, path) for run_id, description, path in DEFAULT_RUNS]
    by_run = {row["run_id"]: row for row in rows}
    r072_fixes = set(by_run["R072"]["fix_tasks"])
    r074_fixes = set(by_run["R074"]["fix_tasks"])
    harms = [set(row["harm_tasks"]) for row in rows]
    common_harms = sorted(set.intersection(*harms)) if harms else []
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "rows": rows,
        "accuracy_cost_frontier": _accuracy_cost_frontier(rows),
        "clean_mechanism_frontier": _clean_mechanism_frontier(rows),
        "stability": {
            "r072_clean_fixes_lost_by_r074": sorted(r072_fixes - r074_fixes),
            "r074_new_fix_not_in_r072": sorted(r074_fixes - r072_fixes),
            "common_harms": common_harms,
        },
        "recommended_next": "distill_clean_fix_preserving_trigger_or_graph_policy",
        "claim_boundary": (
            "R074 is best on accuracy-cost among measured fresh runs, but R069/R072 carry "
            "the clean-fix mechanism signal. The next method should preserve clean fixes "
            "while reducing cost."
        ),
    }


def render_report(payload: Dict[str, Any]) -> str:
    lines = []
    for row in payload["rows"]:
        lines.append(
            "| {run} | {overall} | {baseline} | {clean} | {fix_harm} | {clean_fix_harm} | {runs} | {views} | ${cost:.6f} |".format(
                run=row["run_id"],
                overall=row["overall"],
                baseline=row["baseline"],
                clean=row.get("clean"),
                fix_harm=row.get("fix_harm"),
                clean_fix_harm=row.get("clean_fix_harm"),
                runs=row.get("multiview_run"),
                views=row.get("view_calls"),
                cost=row["cost"],
            )
        )
    return "\n".join(
        [
            "# R075 Fresh Cascade Pareto Report",
            "",
            "## Summary",
            "",
            "| Run | Accuracy | Baseline | Clean | Fix/Harm | Clean Fix/Harm | Triggered | View Calls | Cost |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            *lines,
            "",
            "## Interpretation",
            "",
            f"- Accuracy-cost frontier: `{', '.join(payload['accuracy_cost_frontier'])}`.",
            f"- Clean-mechanism frontier: `{', '.join(payload['clean_mechanism_frontier'])}`.",
            f"- R072 clean fixes lost by R074: `{', '.join(payload['stability']['r072_clean_fixes_lost_by_r074'])}`.",
            f"- R074 new fix not in R072: `{', '.join(payload['stability']['r074_new_fix_not_in_r072'])}`.",
            "",
            payload["claim_boundary"],
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Pareto report for fresh cascade runs.")
    parser.add_argument(
        "--summary-json",
        default="experiment/aqua/res_logs/aqua_tail34_r075_fresh_cascade_pareto_summary.json",
    )
    parser.add_argument(
        "--report-md",
        default="experiment/aqua/run_logs/aqua_tail34_r075_fresh_cascade_pareto_report.md",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    payload = build_fresh_pareto_payload()
    write_json(_absolute(args.summary_json), payload)
    write_text(_absolute(args.report_md), render_report(payload))
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
