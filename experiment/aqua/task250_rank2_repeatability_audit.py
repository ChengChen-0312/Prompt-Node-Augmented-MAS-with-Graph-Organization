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


RULE_NAME = "r104_task250_rank2_repeatability_audit"
CLAIM_BOUNDARY = "task250 rank2 repeatability audit; no new API"

RUN_SOURCES = [
    {
        "run": "R100",
        "path": "experiment/aqua/aqua_tail34_r100_forced_template_rank2_task250_results.jsonl",
    },
    {
        "run": "R103",
        "path": "experiment/aqua/aqua_tail34_r103_rank2_regression_smoke_results.jsonl",
    },
]

DEFAULT_SUMMARY_JSON = "experiment/aqua/res_logs/aqua_tail34_r104_task250_rank2_repeatability_summary.json"
DEFAULT_REPORT_MD = "experiment/aqua/run_logs/aqua_tail34_r104_task250_rank2_repeatability_report.md"


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(_repo_path(path), "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_repeat_rows() -> List[Dict[str, Any]]:
    rows = []
    for source in RUN_SOURCES:
        matches = [row for row in _load_jsonl(source["path"]) if row["task_id"] == "task_250"]
        if len(matches) != 1:
            raise ValueError(f"Expected one task250 row in {source['path']}, got {len(matches)}")
        row = matches[0]
        rows.append(
            {
                "run": source["run"],
                "task_id": row["task_id"],
                "rank": 2,
                "predicted_answer": row["predicted_answer"],
                "true_answer": row["true_answer"],
                "is_solved": bool(row["is_solved"]),
                "source_path": source["path"],
            }
        )
    return rows


def build_repeatability_summary() -> Dict[str, Any]:
    rows = build_repeat_rows()
    predictions = [row["predicted_answer"] for row in rows]
    solved_pattern = [row["is_solved"] for row in rows]
    unique_predictions = sorted(set(predictions))
    return {
        "rule": RULE_NAME,
        "task_id": "task_250",
        "rank": 2,
        "num_repeats": len(rows),
        "predictions": predictions,
        "unique_predictions": unique_predictions,
        "stable_prediction": len(unique_predictions) == 1,
        "solved_pattern": solved_pattern,
        "rows": rows,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def render_report(summary: Dict[str, Any]) -> str:
    table_rows = [
        "| `{run}` | `{pred}` | `{truth}` | `{solved}` | `{path}` |".format(
            run=row["run"],
            pred=row["predicted_answer"],
            truth=row["true_answer"],
            solved=row["is_solved"],
            path=row["source_path"],
        )
        for row in summary["rows"]
    ]
    return "\n".join(
        [
            "# R104 Task250 Rank2 Repeatability Audit",
            "",
            f"**Claim boundary**: {summary['claim_boundary']}",
            "",
            f"- Predictions: `{summary['predictions']}`",
            f"- Unique predictions: `{summary['unique_predictions']}`",
            f"- Stable prediction: `{summary['stable_prediction']}`",
            f"- Solved pattern: `{summary['solved_pattern']}`",
            "",
            "| Run | Prediction | Truth | Solved | Source |",
            "| --- | --- | --- | --- | --- |",
            *table_rows,
            "",
            "## Interpretation",
            "",
            "The same task/template rank is not stable across R100 and R103: it predicts `E` once and "
            "`A` once. Template-rank selection alone is not enough; the next selector needs stability, "
            "consensus, or repeated-evidence checks before deployment.",
            "",
        ]
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit task250 rank2 repeatability across existing runs.")
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    summary = build_repeatability_summary()
    write_json(_repo_path(args.summary_json), summary)
    write_text(_repo_path(args.report_md), render_report(summary))
    print(
        "Built R104 rank2 repeatability audit: "
        f"stable={summary['stable_prediction']} predictions={summary['predictions']}"
    )


if __name__ == "__main__":
    main()
