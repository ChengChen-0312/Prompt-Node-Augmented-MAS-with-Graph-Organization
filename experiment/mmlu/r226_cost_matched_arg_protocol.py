from __future__ import annotations

import argparse
import json
import math
import os
from typing import Any, Dict, List


DEFAULT_TASK_IDS = [
    "MMLU-high_school_statistics_test-32",
    "MMLU-high_school_physics_test-67",
    "MMLU-college_computer_science_test-53",
    "MMLU-conceptual_physics_test-103",
]
DEFAULT_ARG_COST_PER_TASK = 3.042140 / 100.0


def estimate_allowed_requeries(cost_cap: float, arg_cost_per_task: float, max_tasks: int) -> int:
    if arg_cost_per_task <= 0 or cost_cap <= 0 or max_tasks <= 0:
        return 0
    budget_limited = int(math.floor(cost_cap / arg_cost_per_task))
    return max(0, min(int(max_tasks), budget_limited))


def build_cost_matched_manifest(
    task_ids: List[str],
    cost_cap: float,
    arg_cost_per_task: float,
    max_tasks: int,
    source: str,
) -> Dict[str, Any]:
    allowed = estimate_allowed_requeries(cost_cap, arg_cost_per_task, max_tasks)
    selected = list(task_ids[:allowed])
    tasks = [
        {
            "task_id": task_id,
            "baseline_variant": "cost_matched_arg_requery",
            "api_executed": False,
            "estimated_cost": round(float(arg_cost_per_task), 6),
            "source": source,
        }
        for task_id in selected
    ]
    return {
        "task_source": source,
        "requested_task_count": len(task_ids),
        "max_tasks": max_tasks,
        "cost_cap": float(cost_cap),
        "arg_cost_per_task": round(float(arg_cost_per_task), 6),
        "allowed_requeries": allowed,
        "estimated_total_cost": round(sum(row["estimated_cost"] for row in tasks), 6),
        "api_executed": False,
        "tasks": tasks,
        "claim_boundary": "Cost-matched ARG protocol only; no API and no accuracy claim.",
    }


def export_protocol(
    output_json: str,
    report_md: str,
    task_ids: List[str],
    cost_cap: float,
    arg_cost_per_task: float,
    max_tasks: int,
    source: str,
) -> Dict[str, Any]:
    manifest = build_cost_matched_manifest(
        task_ids=task_ids,
        cost_cap=cost_cap,
        arg_cost_per_task=arg_cost_per_task,
        max_tasks=max_tasks,
        source=source,
    )
    summary = {
        "run_id": "R226",
        "title": "Cost-matched ARG re-query protocol",
        "no_api": True,
        **manifest,
        "output_json": output_json,
        "report_md": report_md,
    }

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))

    return summary


def render_report(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R226 Cost-Matched ARG Re-query Protocol",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            "## Budget",
            "",
            f"- Cost cap: `${summary['cost_cap']:.6f}`",
            f"- ARG cost/task estimate: `${summary['arg_cost_per_task']:.6f}`",
            f"- Max tasks: `{summary['max_tasks']}`",
            f"- Allowed re-queries: `{summary['allowed_requeries']}`",
            f"- Estimated total cost: `${summary['estimated_total_cost']:.6f}`",
            "",
            "## Boundary",
            "",
            "This only materializes the cost-matched ARG baseline protocol. It does not spend API budget.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build cost-matched ARG re-query protocol.")
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--report_md", required=True)
    parser.add_argument("--task_ids", nargs="*", default=DEFAULT_TASK_IDS)
    parser.add_argument("--cost_cap", type=float, default=0.45)
    parser.add_argument("--arg_cost_per_task", type=float, default=DEFAULT_ARG_COST_PER_TASK)
    parser.add_argument("--max_tasks", type=int, default=4)
    parser.add_argument("--source", default="R214_candidate_protocol")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = export_protocol(
        output_json=args.output_json,
        report_md=args.report_md,
        task_ids=args.task_ids,
        cost_cap=args.cost_cap,
        arg_cost_per_task=args.arg_cost_per_task,
        max_tasks=args.max_tasks,
        source=args.source,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
