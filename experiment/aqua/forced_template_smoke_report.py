import argparse
import datetime
import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


RULE_NAME = "r084_forced_template_smoke_report"

DEFAULT_SMOKE_RUNS = [
    (
        "rank1_task114_initial",
        "experiment/aqua/aqua_tail34_r084_forced_template_rank1_smoke1_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank1_smoke1_summary.jsonl",
    ),
    (
        "rank5_task114_initial",
        "experiment/aqua/aqua_tail34_r084_forced_template_rank5_smoke1_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank5_smoke1_summary.jsonl",
    ),
    (
        "rank1_task56_initial",
        "experiment/aqua/aqua_tail34_r084_forced_template_rank1_task56_smoke_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank1_task56_smoke_summary.jsonl",
    ),
    (
        "rank1_task114_router_hardened",
        "experiment/aqua/aqua_tail34_r084_forced_template_rank1_router_hardened_smoke1_results.jsonl",
        "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_rank1_router_hardened_smoke1_summary.jsonl",
    ),
]

DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r084_forced_template_smoke_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r084_forced_template_smoke_report.md"


def _load_first_jsonl(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                return json.loads(line)
    raise ValueError(f"No JSONL records in {path}")


def _load_last_jsonl(path: str) -> Dict[str, Any]:
    last = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = json.loads(line)
    if last is None:
        raise ValueError(f"No JSONL records in {path}")
    return last


def _extract_contract_field(text: str, field: str) -> str:
    match = re.search(rf"{field}:\s*([A-Z_/]+)", text or "", flags=re.I)
    return match.group(1).upper() if match else ""


def _router_output(record: Dict[str, Any]) -> str:
    for output in record.get("agent_outputs") or []:
        if output.get("role") == "PN_Router":
            return "\n".join(str(item) for item in output.get("outputs") or [])
    return ""


def _selected_rank(record: Dict[str, Any]) -> int:
    index = int(record.get("selected_candidate_index") or 0)
    candidates = record.get("candidate_graphs") or []
    if index < len(candidates):
        return int(candidates[index].get("rank") or index + 1)
    return index + 1


def _has_promptnode_graph(record: Dict[str, Any]) -> bool:
    roles = (record.get("generated_graph") or {}).get("roles") or []
    return any(str(role).startswith("PN_") for role in roles)


def build_smoke_rows(
    smoke_runs: Sequence[Tuple[str, str, str]] = DEFAULT_SMOKE_RUNS,
) -> List[Dict[str, Any]]:
    rows = []
    for run_name, result_path, summary_path in smoke_runs:
        result = _load_first_jsonl(result_path)
        summary = _load_last_jsonl(summary_path)
        router_text = _router_output(result)
        rows.append(
            {
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
                "router_supported_option": _extract_contract_field(router_text, "SUPPORTED_OPTION"),
                "router_binding_status": _extract_contract_field(router_text, "BINDING_STATUS"),
                "cost": float(summary.get("cost") or 0.0),
                "prompt_tokens": int(summary.get("prompt_tokens") or 0),
                "completion_tokens": int(summary.get("completion_tokens") or 0),
                "result_path": result_path,
                "summary_path": summary_path,
            }
        )
    return rows


def build_smoke_summary(
    smoke_runs: Sequence[Tuple[str, str, str]] = DEFAULT_SMOKE_RUNS,
) -> Dict[str, Any]:
    rows = build_smoke_rows(smoke_runs)
    task_counts: Dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        task_counts[row["task_id"]]["total"] += 1
        task_counts[row["task_id"]]["solved"] += int(row["is_solved"])

    task_outcomes = {
        task_id: {
            "best_result": f"{counts['solved']}/{counts['total']}",
            "num_runs": counts["total"],
        }
        for task_id, counts in sorted(task_counts.items())
    }
    return {
        "rule": RULE_NAME,
        "timestamp": datetime.datetime.now().isoformat(),
        "num_smoke_runs": len(rows),
        "solved_runs": sum(1 for row in rows if row["is_solved"]),
        "promptnode_graph_runs": sum(1 for row in rows if row["has_promptnode_graph"]),
        "router_status_counts": dict(Counter(row["router_binding_status"] for row in rows)),
        "router_supported_option_counts": dict(Counter(row["router_supported_option"] for row in rows)),
        "task_outcomes": task_outcomes,
        "total_cost": sum(row["cost"] for row in rows),
        "total_prompt_tokens": sum(row["prompt_tokens"] for row in rows),
        "total_completion_tokens": sum(row["completion_tokens"] for row in rows),
        "rows": rows,
        "claim_boundary": (
            "R084 is smoke-only evidence for forced-template execution plumbing and qualitative failure analysis. "
            "It is not a tail34 accuracy result and does not justify full-run claims."
        ),
    }


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


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{run}` | `{task}` | `{rank}` | `{pred}` | `{gold}` | `{ok}` | `{router}` | `${cost:.6f}` |".format(
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
            "# R084 Forced-Template PromptNode Smoke Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Smoke runs: `{summary['num_smoke_runs']}`",
            f"- Solved runs: `{summary['solved_runs']}`",
            f"- PromptNode graph runs: `{summary['promptnode_graph_runs']}`",
            f"- Router status counts: `{summary['router_status_counts']}`",
            f"- Total smoke cost: `${summary['total_cost']:.6f}`",
            "",
            "| Run | Task | Rank | Prediction | Gold | Solved | Router contract | Cost |",
            "| --- | --- | ---: | --- | --- | --- | --- | ---: |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "The forced-template execution hook is functional: every smoke run executed an explicit PromptNode graph before "
            "final aggregation. The smoke results do not justify a full tail34 run yet. `task_56` succeeds, but `task_114` "
            "shows that noisy/unsupported boundary cases require stronger routing or abstention logic; after router-contract "
            "hardening, the router no longer emits an erroneous `C/EXACT_MATCH`, but the system still does not recover the "
            "official label `D` from weak evidence.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize R084 forced-template smoke runs.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_smoke_summary()
    write_json(args.summary_json, summary)
    write_text(args.report_md, render_report(summary))
    print(
        "Built forced-template smoke report: "
        f"runs={summary['num_smoke_runs']} solved={summary['solved_runs']} "
        f"cost=${summary['total_cost']:.6f}"
    )


if __name__ == "__main__":
    main()
