import argparse
import datetime
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_smoke_report import (  # noqa: E402
    _extract_contract_field,
    _has_promptnode_graph,
    _load_first_jsonl,
    _load_last_jsonl,
    _router_output,
    _selected_rank,
    write_json,
    write_text,
)


RULE_NAME = "r085_forced_template_clean_positive_smoke"
CLAIM_BOUNDARY = "clean-positive smoke only, not tail34 accuracy"

DEFAULT_CLEAN_POSITIVE_RUNS = [
    (
        "task56_clean_positive",
        "experiment/aqua/aqua_tail34_r084_forced_template_rank1_task56_smoke_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank1_task56_smoke_summary.jsonl",
    ),
    (
        "task188_clean_positive",
        "experiment/aqua/aqua_tail34_r085_forced_template_rank1_task188_smoke_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r085_forced_template_rank1_task188_smoke_summary.jsonl",
    ),
    (
        "task8_clean_positive",
        "experiment/aqua/aqua_tail34_r085_forced_template_rank1_task8_smoke_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r085_forced_template_rank1_task8_smoke_summary.jsonl",
    ),
]

DEFAULT_BOUNDARY_RUNS = [
    (
        "task114_noisy_boundary_router_hardened",
        "experiment/aqua/aqua_tail34_r084_forced_template_rank1_router_hardened_smoke1_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank1_router_hardened_smoke1_summary.jsonl",
    ),
]

DEFAULT_SUMMARY_JSON = (
    "experiment/aqua/res_logs/aqua_tail34_r085_forced_template_clean_positive_summary.json"
)
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r085_forced_template_clean_positive_report.md"


def _repo_path(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)


def _build_rows(
    run_group: str,
    runs: Sequence[Tuple[str, str, str]],
) -> List[Dict[str, Any]]:
    rows = []
    for run_name, result_path, summary_path in runs:
        result = _load_first_jsonl(_repo_path(result_path))
        summary = _load_last_jsonl(_repo_path(summary_path))
        router_text = _router_output(result)
        rows.append(
            {
                "run_group": run_group,
                "run_name": run_name,
                "task_id": result.get("task_id"),
                "true_answer": result.get("true_answer"),
                "predicted_answer": result.get("predicted_answer"),
                "is_solved": bool(result.get("is_solved")),
                "selected_rank": _selected_rank(result),
                "roles": (result.get("generated_graph") or {}).get("roles") or [],
                "num_nodes": result.get("num_nodes"),
                "num_edges": result.get("num_edges"),
                "has_promptnode_graph": _has_promptnode_graph(result),
                "router_supported_option": _extract_contract_field(
                    router_text, "SUPPORTED_OPTION"
                ),
                "router_binding_status": _extract_contract_field(
                    router_text, "BINDING_STATUS"
                ),
                "cost": float(summary.get("cost") or 0.0),
                "prompt_tokens": int(summary.get("prompt_tokens") or 0),
                "completion_tokens": int(summary.get("completion_tokens") or 0),
                "result_path": result_path,
                "summary_path": summary_path,
            }
        )
    return rows


def build_clean_positive_summary(
    clean_positive_runs: Sequence[Tuple[str, str, str]] = DEFAULT_CLEAN_POSITIVE_RUNS,
    boundary_runs: Sequence[Tuple[str, str, str]] = DEFAULT_BOUNDARY_RUNS,
) -> Dict[str, Any]:
    clean_rows = _build_rows("clean_positive", clean_positive_runs)
    boundary_rows = _build_rows("boundary", boundary_runs)
    rows = clean_rows + boundary_rows

    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "clean_positive_runs": len(clean_rows),
        "clean_positive_solved": sum(1 for row in clean_rows if row["is_solved"]),
        "boundary_runs": len(boundary_rows),
        "boundary_solved": sum(1 for row in boundary_rows if row["is_solved"]),
        "promptnode_graph_runs": sum(1 for row in rows if row["has_promptnode_graph"]),
        "router_status_counts": dict(Counter(row["router_binding_status"] for row in rows)),
        "router_supported_option_counts": dict(
            Counter(row["router_supported_option"] for row in rows)
        ),
        "clean_positive_cost": sum(row["cost"] for row in clean_rows),
        "boundary_cost": sum(row["cost"] for row in boundary_rows),
        "total_cost": sum(row["cost"] for row in rows),
        "total_prompt_tokens": sum(row["prompt_tokens"] for row in rows),
        "total_completion_tokens": sum(row["completion_tokens"] for row in rows),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{group}` | `{run}` | `{task}` | `{rank}` | `{pred}` | `{gold}` | `{ok}` | `{router}` | `${cost:.6f}` |".format(
            group=row["run_group"],
            run=row["run_name"],
            task=row["task_id"],
            rank=row["selected_rank"],
            pred=row["predicted_answer"],
            gold=row["true_answer"],
            ok="yes" if row["is_solved"] else "no",
            router=f"{row['router_supported_option']}/{row['router_binding_status']}",
            cost=row["cost"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R085 Forced-Template Clean-Positive Smoke Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Clean-positive smoke runs: `{summary['clean_positive_runs']}`",
            f"- Clean-positive solved: `{summary['clean_positive_solved']}`",
            f"- Boundary smoke runs: `{summary['boundary_runs']}`",
            f"- Boundary solved: `{summary['boundary_solved']}`",
            f"- PromptNode graph runs: `{summary['promptnode_graph_runs']}`",
            f"- Router status counts: `{summary['router_status_counts']}`",
            f"- Clean-positive cost: `${summary['clean_positive_cost']:.6f}`",
            f"- Total smoke cost: `${summary['total_cost']:.6f}`",
            "",
            "| Group | Run | Task | Rank | Prediction | Gold | Solved | Router contract | Cost |",
            "| --- | --- | --- | ---: | --- | --- | --- | --- | ---: |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "Rank-1 forced-template PromptNode execution preserves the three clean-positive smoke cases, "
            "but the hardened noisy boundary case still fails. This supports a narrow execution and "
            "case-selection claim only. It does not establish tail34 accuracy or improvement over the "
            "historical ARG-Designer run.",
            "",
            "The next experiment should turn this observation into a pre-registered gate: allow explicit "
            "PromptNode templates on cleanly bound cases, and suppress or fall back on weak/noisy "
            "boundary cases before spending on a broader held-out run.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize R085 clean-positive smoke runs.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_clean_positive_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built forced-template clean-positive report: "
        f"clean={summary['clean_positive_solved']}/{summary['clean_positive_runs']} "
        f"boundary={summary['boundary_solved']}/{summary['boundary_runs']} "
        f"cost=${summary['total_cost']:.6f}"
    )


if __name__ == "__main__":
    main()
