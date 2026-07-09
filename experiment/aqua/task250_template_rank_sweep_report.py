import argparse
import json
import os
import sys
from typing import Any, Dict, List


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.aqua.forced_template_gate_r058_stress import _repo_path  # noqa: E402
from experiment.aqua.forced_template_smoke_report import write_json, write_text  # noqa: E402


RULE_NAME = "r100_task250_template_rank_sweep_report"
CLAIM_BOUNDARY = "one-task task250 rank sweep; not held-out accuracy"
SWEEP_RANKS = [2, 3, 4, 5]
DESIRED_PREDICTION = "E"

DEFAULT_OUTPUT_JSON = "experiment/aqua/res_logs/aqua_tail34_r100_task250_template_rank_sweep_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r100_task250_template_rank_sweep_report.md"
DEFAULT_COMBINED_JSONL = "experiment/aqua/aqua_tail34_r100_task250_template_rank_sweep_rows.jsonl"


def _result_path(rank: int) -> str:
    return f"experiment/aqua/aqua_tail34_r100_forced_template_rank{rank}_task250_results.jsonl"


def _summary_path(rank: int) -> str:
    return f"experiment/aqua/res_logs/aqua_tail34_r100_forced_template_rank{rank}_task250_summary.jsonl"


def _read_last_jsonl(path: str) -> Dict[str, Any]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    if not rows:
        raise ValueError(f"No rows found in {path}")
    return rows[-1]


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    abs_path = _repo_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_rank_rows() -> List[Dict[str, Any]]:
    rows = []
    for rank in SWEEP_RANKS:
        result = _read_last_jsonl(_result_path(rank))
        summary = _read_last_jsonl(_summary_path(rank))
        predicted = result.get("predicted_answer")
        rows.append(
            {
                "task_id": "task_250",
                "rank": rank,
                "predicted_answer": predicted,
                "desired_prediction": DESIRED_PREDICTION,
                "matches_desired_prediction": predicted == DESIRED_PREDICTION,
                "is_solved": bool(result.get("is_solved")),
                "true_answer": result.get("true_answer"),
                "cost": float(summary.get("cost", 0.0)),
                "prompt_tokens": int(summary.get("prompt_tokens", 0)),
                "completion_tokens": int(summary.get("completion_tokens", 0)),
                "result_path": _result_path(rank),
                "summary_path": _summary_path(rank),
            }
        )
    return rows


def build_rank_sweep_summary() -> Dict[str, Any]:
    rows = build_rank_rows()
    matching = [row["rank"] for row in rows if row["matches_desired_prediction"]]
    nonmatching = [row["rank"] for row in rows if not row["matches_desired_prediction"]]
    return {
        "rule": RULE_NAME,
        "task_id": "task_250",
        "desired_prediction": DESIRED_PREDICTION,
        "sweep_ranks": SWEEP_RANKS,
        "matching_ranks": matching,
        "nonmatching_ranks": nonmatching,
        "best_matching_rank": min(matching) if matching else None,
        "num_matching_ranks": len(matching),
        "total_cost": sum(row["cost"] for row in rows),
        "total_prompt_tokens": sum(row["prompt_tokens"] for row in rows),
        "total_completion_tokens": sum(row["completion_tokens"] for row in rows),
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{rank}` | `{pred}` | `{match}` | `{solved}` | `${cost:.6f}` | `{pt}` | `{ct}` |".format(
            rank=row["rank"],
            pred=row["predicted_answer"],
            match=row["matches_desired_prediction"],
            solved=row["is_solved"],
            cost=row["cost"],
            pt=row["prompt_tokens"],
            ct=row["completion_tokens"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R100 Task250 Template Rank Sweep Report",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Task: `{summary['task_id']}`",
            f"- Desired prediction: `{summary['desired_prediction']}`",
            f"- Sweep ranks: `{summary['sweep_ranks']}`",
            f"- Matching ranks: `{summary['matching_ranks']}`",
            f"- Non-matching ranks: `{summary['nonmatching_ranks']}`",
            f"- Best matching rank: `{summary['best_matching_rank']}`",
            f"- Total cost: `${summary['total_cost']:.6f}`",
            "",
            "| Rank | Prediction | Matches desired | Solved | Cost | Prompt tokens | Completion tokens |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "Ranks 2 and 5 recover the clean `task_250` target prediction `E`, while ranks 3 and 4 "
            "fall back to `A`. This gives a concrete template-rank candidate for the next clean-safe "
            "smoke, but it is a one-task search and cannot be reported as held-out accuracy.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize task250 rank2-rank5 template sweep.")
    parser.add_argument("--summary-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--combined-jsonl", default=DEFAULT_COMBINED_JSONL)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    rows = build_rank_rows()
    _write_jsonl(args.combined_jsonl, rows)
    summary = build_rank_sweep_summary()
    summary["combined_jsonl"] = args.combined_jsonl
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R100 task250 rank sweep report: "
        f"matching={summary['matching_ranks']} total_cost=${summary['total_cost']:.6f}"
    )


if __name__ == "__main__":
    main()
