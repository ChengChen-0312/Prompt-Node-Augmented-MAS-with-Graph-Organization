from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from experiment.mmlu.r222_control_manifest_leakage_scan import scan_control_rows


VALID_LABELS = {"A", "B", "C", "D", "E"}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def adapt_router_record(row: Dict[str, Any]) -> Dict[str, Any]:
    action = str(row.get("router_action", "abstain"))
    label = str(row.get("target_option_label", "NONE")).strip().upper()
    would_switch = action == "switch_to_objective" and label in VALID_LABELS
    schema = row.get("router_final_schema", {})
    leakage = scan_control_rows([row])
    return {
        "task_id": row.get("task_id"),
        "split_role": row.get("split_role"),
        "control_variant": row.get("control_variant", "proposed_router_final"),
        "router_action": action if would_switch else "abstain",
        "selected_label": label if would_switch else "NONE",
        "would_switch": would_switch,
        "uses_promptedge_text": bool(
            schema.get("promptedge_text_policy", {}).get("edge_text_as_prompt", True)
        ),
        "leakage_pass": leakage["leakage_pass"],
        "leakage_violations": leakage["leakage_violations"],
    }


def summarize_adapter_outputs(outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "records": len(outputs),
        "would_switch": sum(1 for row in outputs if row["would_switch"]),
        "leakage_violations": sum(row["leakage_violations"] for row in outputs),
        "leakage_pass": all(row["leakage_pass"] for row in outputs),
        "variant_counts": dict(sorted(Counter(row["control_variant"] for row in outputs).items())),
        "split_counts": dict(sorted(Counter(str(row.get("split_role", "")) for row in outputs).items())),
    }


def run_adapter_dry_run(input_paths: List[str], output_jsonl: str, summary_json: str, report_md: str) -> Dict[str, Any]:
    outputs: List[Dict[str, Any]] = []
    path_counts: Dict[str, int] = {}
    for path in input_paths:
        rows = load_jsonl(path)
        path_counts[path] = len(rows)
        outputs.extend(adapt_router_record(row) for row in rows)

    summary = summarize_adapter_outputs(outputs)
    summary.update(
        {
            "run_id": "R223",
            "title": "Router-final adapter dry-run",
            "claim_boundary": "Local adapter dry-run only; no API and no accuracy claim.",
            "no_api": True,
            "input_paths": input_paths,
            "input_path_counts": path_counts,
            "output_jsonl": output_jsonl,
        }
    )

    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for row in outputs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    os.makedirs(os.path.dirname(summary_json), exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(report_md), exist_ok=True)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))

    return summary


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R223 Router-Final Adapter Dry-Run",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        "## Result",
        "",
        f"- Input files: `{len(summary['input_paths'])}`",
        f"- Records: `{summary['records']}`",
        f"- Would switch: `{summary['would_switch']}`",
        f"- Leakage violations: `{summary['leakage_violations']}`",
        f"- Leakage pass: `{summary['leakage_pass']}`",
        f"- Variants: `{summary['variant_counts']}`",
        "",
        "## Boundary",
        "",
        "The adapter only maps manifest rows to local switch/abstain decisions. It does not call an LLM and does not evaluate answer accuracy.",
        "",
    ]
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run router-final adapter over manifests.")
    parser.add_argument("--input_paths", nargs="+", required=True)
    parser.add_argument("--output_jsonl", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    expanded_paths: List[str] = []
    for pattern in args.input_paths:
        matches = sorted(glob.glob(pattern))
        expanded_paths.extend(matches or [pattern])
    summary = run_adapter_dry_run(
        input_paths=expanded_paths,
        output_jsonl=args.output_jsonl,
        summary_json=args.summary_json,
        report_md=args.report_md,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
