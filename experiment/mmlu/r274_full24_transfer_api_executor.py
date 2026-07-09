from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r253_mmlu_transfer_api_executor import execute_transfer_diagnostic


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R274 MMLU Full24 Transfer API Diagnostic",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- Records: `{summary['records']}`",
        f"- Evaluated records: `{summary['evaluated_records']}`",
        f"- API required/executed/errors: `{summary['api_required']}/{summary['api_executed']}/{summary['api_errors']}`",
        f"- Correct: `{summary['correct']}`",
        f"- Accuracy: `{summary['accuracy']}`",
        f"- Fixes/harms vs ARG baseline: `{summary['fixes']}` / `{summary['harms']}`",
        f"- Cost: `${summary['api_cost']:.6f}`",
        f"- Prompt/completion tokens: `{summary['prompt_tokens']}/{summary['completion_tokens']}`",
        "",
        "## By Variant",
        "",
        "| Variant | Records | Correct | Accuracy | Fix/Harm | API executed/errors |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for variant, item in summary["by_variant"].items():
        rows.append(
            f"| `{variant}` | `{item['records']}` | `{item['correct']}` | `{item['accuracy']}` | `{item['fixes']}/{item['harms']}` | `{item['api_executed']}/{item['api_errors']}` |"
        )
    rows.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a same-model full24 diagnostic. It is broader than tiny16 but still not a definitive SCI-Q2 transfer result until selector replay and claim audit are complete.",
            "",
        ]
    )
    return "\n".join(rows)


async def run_async(
    records_jsonl: str = "experiment/mmlu/run_logs/mmlu_r273_full24_transfer_preflight_records.jsonl",
    preflight_json: str = "experiment/mmlu/res_logs/mmlu_r273_full24_transfer_preflight_summary.json",
    env_file: str = "/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env",
    output_jsonl: str = "experiment/mmlu/run_logs/mmlu_r274_full24_transfer_api_results.jsonl",
    summary_json: str = "experiment/mmlu/res_logs/mmlu_r274_full24_transfer_api_summary.json",
    report_md: str = "experiment/mmlu/run_logs/mmlu_r274_full24_transfer_api_report.md",
    execute_api: bool = False,
) -> Dict[str, Any]:
    if not execute_api:
        raise RuntimeError("Pass --execute_api to run R274.")
    summary = await execute_transfer_diagnostic(
        records_jsonl=records_jsonl,
        preflight_json=preflight_json,
        env_file=env_file,
        output_jsonl=output_jsonl,
        summary_json=summary_json,
        report_md=report_md,
        execute_api=True,
    )
    summary.update(
        {
            "run_id": "R274",
            "title": "MMLU full24 transfer API diagnostic",
            "claim_boundary": "Full24 same-model diagnostic only; selector replay and claim audit required before transfer claims.",
            "records_jsonl": records_jsonl,
            "preflight_json": preflight_json,
            "output_jsonl": output_jsonl,
            "summary_json": summary_json,
            "report_md": report_md,
        }
    )
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))
    return summary


def run(**kwargs: Any) -> Dict[str, Any]:
    return asyncio.run(run_async(**kwargs))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute R274 MMLU full24 transfer diagnostic.")
    parser.add_argument("--records_jsonl", default="experiment/mmlu/run_logs/mmlu_r273_full24_transfer_preflight_records.jsonl")
    parser.add_argument("--preflight_json", default="experiment/mmlu/res_logs/mmlu_r273_full24_transfer_preflight_summary.json")
    parser.add_argument("--env_file", default="/Users/chencheng/Downloads/论文/OpenG-MAS_benchmark_code_release/benchmark_config/.env")
    parser.add_argument("--output_jsonl", default="experiment/mmlu/run_logs/mmlu_r274_full24_transfer_api_results.jsonl")
    parser.add_argument("--summary_json", default="experiment/mmlu/res_logs/mmlu_r274_full24_transfer_api_summary.json")
    parser.add_argument("--report_md", default="experiment/mmlu/run_logs/mmlu_r274_full24_transfer_api_report.md")
    parser.add_argument("--execute_api", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
