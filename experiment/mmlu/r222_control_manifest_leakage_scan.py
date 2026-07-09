from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter
from typing import Any, Dict, List


DEFAULT_FORBIDDEN_FIELDS = {
    "task_id",
    "answer",
    "true_answer",
    "gold_answer",
    "is_correct",
    "correctness",
    "audit_label",
    "analysis",
    "clean_label",
    "gold_binding_status",
    "rationale_issue",
}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _schema_forbidden(row: Dict[str, Any]) -> set[str]:
    schema = row.get("router_final_schema", {})
    return set(schema.get("forbidden_model_visible_fields", [])) | DEFAULT_FORBIDDEN_FIELDS


def scan_control_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    violations: List[Dict[str, Any]] = []
    variant_counts = Counter(str(row.get("control_variant", "")) for row in rows)
    action_counts = Counter(str(row.get("router_action", "")) for row in rows)

    for idx, row in enumerate(rows):
        forbidden = _schema_forbidden(row)
        input_keys = set(row.get("model_visible_input", {}).keys())
        input_overlap = sorted(input_keys & forbidden)
        if input_overlap:
            violations.append(
                {
                    "row_index": idx,
                    "reason": "model_visible_input_forbidden_fields",
                    "fields": input_overlap,
                }
            )

        schema = row.get("router_final_schema", {})
        schema_visible = set(schema.get("model_visible_fields", []))
        normalized_schema_visible = {
            field.split(".", 1)[-1] if "." in field else field
            for field in schema_visible
        }
        schema_overlap = sorted(normalized_schema_visible & forbidden)
        if schema_overlap:
            violations.append(
                {
                    "row_index": idx,
                    "reason": "schema_visible_forbidden_fields",
                    "fields": schema_overlap,
                }
            )
        if schema.get("gold_answer_used") is not False:
            violations.append(
                {
                    "row_index": idx,
                    "reason": "gold_answer_used_not_false",
                    "value": schema.get("gold_answer_used"),
                }
            )

    return {
        "records": len(rows),
        "variants": dict(sorted(variant_counts.items())),
        "router_actions": dict(sorted(action_counts.items())),
        "leakage_violations": len(violations),
        "leakage_pass": len(violations) == 0,
        "violations": violations,
    }


def scan_manifest_dir(input_dir: str) -> Dict[str, Any]:
    files = sorted(glob.glob(os.path.join(input_dir, "*.jsonl")))
    per_file: Dict[str, Dict[str, Any]] = {}
    total_violations = 0
    total_records = 0
    for path in files:
        rows = load_jsonl(path)
        summary = scan_control_rows(rows)
        per_file[os.path.basename(path)] = summary
        total_records += summary["records"]
        total_violations += summary["leakage_violations"]
    return {
        "input_dir": input_dir,
        "files": len(files),
        "records": total_records,
        "leakage_violations": total_violations,
        "leakage_pass": total_violations == 0,
        "per_file": per_file,
    }


def render_report(summary: Dict[str, Any]) -> str:
    rows = [
        "# R222 Control Manifest Leakage Scan",
        "",
        "**Claim boundary**: leakage scan only. No API evaluation and no accuracy claim.",
        "",
        "## Result",
        "",
        f"- Input dir: `{summary['input_dir']}`",
        f"- Files: `{summary['files']}`",
        f"- Records: `{summary['records']}`",
        f"- Leakage violations: `{summary['leakage_violations']}`",
        f"- Leakage pass: `{summary['leakage_pass']}`",
        "",
        "| File | Records | Violations | Pass |",
        "|---|---:|---:|---|",
    ]
    for name, item in summary["per_file"].items():
        rows.append(
            f"| `{name}` | `{item['records']}` | `{item['leakage_violations']}` | `{item['leakage_pass']}` |"
        )
    rows.extend(
        [
            "",
            "## Boundary",
            "",
            "The scan checks model-visible control inputs and schema-visible fields for forbidden answer, correctness, task-id, and audit fields. It does not run any model.",
            "",
        ]
    )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan router-final control manifests for leakage.")
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--summary_json", required=True)
    parser.add_argument("--report_md", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = scan_manifest_dir(args.input_dir)
    summary.update(
        {
            "run_id": "R222",
            "title": "Router-final control manifest leakage scan",
            "claim_boundary": "Leakage scan only; no API and no accuracy claim.",
            "no_api": True,
        }
    )

    os.makedirs(os.path.dirname(args.summary_json), exist_ok=True)
    with open(args.summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(args.report_md), exist_ok=True)
    with open(args.report_md, "w", encoding="utf-8") as f:
        f.write(render_report(summary))

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
